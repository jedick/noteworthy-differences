import requests
from datetime import datetime, timedelta
from typing import Dict, Optional
import re


def run_get_request(params: dict):
    """
    Utility function to run GET request against Wikipedia API
    """
    base_url = "https://en.wikipedia.org/w/api.php"

    # We need to supply headers for the request to work
    headers = {
        "User-Agent": f"NoteworthyDifferences/1.0 (j3ffdick@gmail.com) requests/{requests.__version__}"
    }

    response = requests.get(base_url, params=params, headers=headers)
    # Handle HTTP errors
    response.raise_for_status()

    try:
        json_data = response.json()
    except Exception:
        raise ValueError(f"Unable to parse response: {response}")

    return json_data


def extract_revision_info(json_data, revnum=0, limit_revnum=True):
    """
    Utility function to extract page revision info from JSON data returned from API call

    Args:
        revnum: revision before current

    Examples:
        title = 'David_Szalay'
        json_data = get_previous_revisions(title, revisions = 100)
        extract_revision_info(json_data)       # Current revision
        extract_revision_info(json_data, 10)   # 10th revision before current
        extract_revision_info(json_data, 100)  # 10th revision before current
    """
    # Extract page and revision info
    pages = json_data["query"]["pages"]
    page_id = list(pages.keys())[0]

    try:
        if limit_revnum:
            # Limit revnum to earliest available revision before current
            revnum = min([revnum, len(pages[page_id]["revisions"]) - 1])
        # Get the specified revision
        revision = pages[page_id]["revisions"][revnum]
        # Remove the parentid key because we don't use it
        _ = revision.pop("parentid", None)
        # Add the actual revision number
        revision["revnum"] = revnum
        return revision
    except:
        # Page or revision not found, return empty dict
        return {"revid": None, "timestamp": None, "revnum": None}


def get_revision_from_age(title: str, age_days: int = 0) -> Dict[str, str]:
    """
    Get the revision info of a Wikipedia article closest to the age in days.

    Args:
        title: Wikipedia article title (e.g., 'David_Szalay')
        age_days: Age of the article revision in days (0 for current)

    Returns:
        Dictionary containing:
        - 'revid': Revision id of the article revision
        - 'timestamp': Timestamp of the article revision
    """

    # Get the target date
    target_date = datetime.utcnow() - timedelta(days=age_days)

    # Get the revision closest to the target date
    params = {
        "action": "query",
        "titles": title,
        "prop": "revisions",
        "rvlimit": 1,
        "rvdir": "older",
        "rvstart": target_date.isoformat() + "Z",
        "rvprop": "ids|timestamp",
        "format": "json",
    }

    # Run GET request
    json_data = run_get_request(params)

    # Return revision info
    return extract_revision_info(json_data)


def get_previous_revisions(title: str, revisions: int = 0) -> Dict[str, str]:
    """
    Get the revision info of a Wikipedia article a certain number of revisions before the current one.

    Args:
        title: Wikipedia article title (e.g., 'David_Szalay')
        revision: What revision before current (0 for current, must be between 0 and 499)

    Returns:
        Dictionary containing:
        - 'revid': Revision id of the article revision
        - 'timestamp': Timestamp of the article revision

    Note:
        In the Wikipedia API, rvlimit is how many revisions will be returned and must be between 1 and 500
        rvlimit = 1 returns a single revision: the current one
        rvlimit = 101 returns the 100 most recent revisions and the current one
        This is why we use rvlimit = revision + 1
    """

    # Get the revision closest to the target date
    params = {
        "action": "query",
        "prop": "revisions",
        "titles": title,
        "rvlimit": revisions + 1,
        "rvdir": "older",
        "rvprop": "ids|timestamp",
        "format": "json",
    }

    # Run GET request
    json_data = run_get_request(params)

    # Return info for all revisions
    return json_data


def get_wikipedia_introduction(revid: int) -> Dict[str, str]:
    """
    Retrieve the introduction of a Wikipedia article.

    Args:
        revid: Revision id of the article

    Returns:
        Text of the introduction

    Example:
        # Get intro from current article revision
        revision_info = get_revision_from_age("David_Szalay")
        get_wikipedia_introduction(revision_info["revid"])
    """

    # Return None for missing revid
    if not revid:
        return None

    # Get the content of this specific revision
    params = {"action": "parse", "oldid": revid, "prop": "text", "format": "json"}

    json_data = run_get_request(params)

    # Sometimes a revision is deleted and can't be viewed
    # E.g. revid = '1276494621' for Turin
    try:
        html_content = json_data["parse"]["text"]["*"]
    except:
        return None

    # Extract introduction (text before first section heading)
    # Remove everything from the first <h2> tag onwards
    intro_html = re.split(r"<h2", html_content, maxsplit=1)[0]

    # Extract text from paragraphs, excluding certain elements
    from html.parser import HTMLParser

    class IntroParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.text = []
            self.in_p = False
            self.skip = False

        def handle_starttag(self, tag, attrs):
            if tag == "p":
                self.in_p = True
            # Skip certain elements
            if tag in ["style", "script", "table", "div"]:
                attrs_dict = dict(attrs)
                # Skip infoboxes, navboxes, etc.
                if "class" in attrs_dict:
                    if any(
                        x in attrs_dict["class"]
                        for x in ["infobox", "navbox", "metadata", "toc"]
                    ):
                        self.skip = True
                if tag in ["style", "script"]:
                    self.skip = True

        def handle_endtag(self, tag):
            if tag == "p":
                if self.in_p and self.text and not self.text[-1].endswith("\n\n"):
                    self.text.append("\n\n")
                self.in_p = False
            if tag in ["style", "script", "table", "div"]:
                self.skip = False

        def handle_data(self, data):
            if self.in_p and not self.skip:
                # *Don't* clean up whitespace here - it makes run-on words
                # text = " ".join(data.split())
                text = data
                if text:
                    self.text.append(text)

    parser = IntroParser()
    parser.feed(intro_html)

    # Join and clean up the text
    introduction = "".join(parser.text).strip()

    # Remove multiple newlines
    introduction = re.sub(r"\n{3,}", "\n\n", introduction)

    # Remove empty paragraphs
    paragraphs = [p.strip() for p in introduction.split("\n\n") if p.strip()]
    introduction = "\n\n".join(paragraphs)

    return introduction


def get_revisions_behind(title: str, revid: int) -> int:
    """
    Get the number of revisions a given revid is behind the current revision of the page.

    Args:
        revid: Revision ID of the page

    Returns:
        Integer representing the number of revisions back (0 if it's the current revision)

    Example:
        # Get how many revisions behind a specific revid is
        revisions_behind = get_revisions_behind(123456789)
    """

    ## First, get the page title from the revid
    # params = {"action": "parse", "oldid": revid, "prop": "title", "format": "json"}
    # try:
    #    json_data = run_get_request(params)
    #    title = json_data["parse"]["title"]
    # except Exception:
    #    # If we can't get the title, the revid might be invalid
    #    raise ValueError(f"Could not retrieve page title for revid {revid}. The revid may be invalid or deleted.")

    # Search through revisions going back from current
    # We'll paginate through results if needed
    revision_count = 0
    continue_token = None

    # Run the loop twice to get up to 1000 revisions behind
    for i in range(2):
        params = {
            "action": "query",
            "titles": title,
            "prop": "revisions",
            "rvlimit": 500,  # API limit per request
            "rvdir": "older",
            "rvprop": "ids",
            "format": "json",
        }

        if continue_token:
            params["rvcontinue"] = continue_token

        try:
            json_data = run_get_request(params)
            pages = json_data["query"]["pages"]
            page_id = list(pages.keys())[0]

            if page_id == "-1":
                raise ValueError(f"Page not found for revid {revid}")

            revisions = pages[page_id]["revisions"]

            # Find the index of the given revid in the current batch of revisions
            for i, revision in enumerate(revisions):
                if revision["revid"] == revid:
                    return revision_count + i

            # Update the count of revisions we've checked
            revision_count += len(revisions)

            # Check if there are more revisions to search
            continue_token = json_data.get("continue", {}).get("rvcontinue")

            if not continue_token:
                # Reached the end of revisions but didn't find the revid
                raise ValueError(
                    f"Revid {revid} not found in the revision history of the page. "
                    f"It may be from a different page or may have been deleted."
                )

        except ValueError:
            # Re-raise ValueError exceptions
            raise
        except Exception as e:
            raise ValueError(f"Error searching for revid {revid}: {e}")

    # If we looped without returning the revision count, return it as a negative number
    negative_revision_count = -revision_count
    return negative_revision_count


def get_random_wikipedia_title():
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "list": "random",
        "rnnamespace": 0,
        "rnlimit": 1,
        "format": "json",
    }

    try:
        json_data = run_get_request(params)

        # Extract the title
        title = json_data["query"]["random"][0]["title"]
        return title

    except requests.RequestException as e:
        print(f"Error fetching random Wikipedia title: {e}")
        return None
