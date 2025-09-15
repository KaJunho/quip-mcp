# Copyright 2025 Amazon.com, Inc. or its affiliates. All Rights Reserved.

import quip
import os, json, datetime
import html, unicodedata, re
from markdownify import markdownify as md
from mcp.server.fastmcp import FastMCP
from bs4 import BeautifulSoup


# Get token from environment variables
access_token = os.environ.get('QUIP_ACCESS_TOKEN', "")
base_url = os.environ.get('QUIP_BASE_URL', "https://platform.quip-amazon.com")

mcp = FastMCP("quip-browse-server")


def init_quip_client():
    """
    Initialize and return a Quip client instance.
    Gets access token and base URL from environment variables, creates an authenticated Quip client,
    verifies authentication status and returns a usable client object.
    """
    
    if not access_token or not base_url:
        raise ValueError("QUIP_ACCESS_TOKEN environment variable is required")

    client = quip.QuipClient(
        access_token=access_token,
        base_url=base_url,
        request_timeout=20  # Increased timeout
    )

    # Verify authentication
    try:
        user = client.get_authenticated_user()
        print(f"Successfully authenticated as user: {user.get('name', 'Unknown')}")
    except Exception as e:
        print(f"Authentication failed: {str(e)}")
        raise

    return client


def get_document_content(thread_id):
    """
    Retrieve document content for a specified thread.
    Returns a JSON string containing thread ID, type, title, and HTML content converted to Markdown format.
    """
    try:
        client = init_quip_client()
        doc = client.get_thread(thread_id)
        thread = doc["thread"]
        content = {
            "thread_id": thread["id"], 
            "thread_type": thread["type"],
            "thread_title": thread["title"],
            "thread_html_content": md(doc['html'], heading_style="ATX")
            }
        return json.dumps(content)
    except Exception as e:
        raise


def get_username_by_id(id):
    """
    Get username by user ID.
    Queries the Quip API to retrieve the username corresponding to the specified user ID.
    """
    try:
        client = init_quip_client()
        username = client.get_user(id)["name"]
        return username
    except Exception as e:
        raise


def get_section_bs(section_id, thread_id=None, document_html=None):
    """
    Get a BeautifulSoup element for a specified section in the document.
    Can retrieve document content by providing either document_html or thread_id.
    Returns the HTML element object matching the section_id.
    """
    if not document_html:
        client = init_quip_client()
        document_html = client.get_thread(thread_id).get("html")
        if not document_html:
            return None
    soup = parse_document_html_bs(document_html)
    element = soup.find(id=section_id)
    return element


def clean_extracted_text(text):
    """
    Clean text content extracted from BeautifulSoup.
    Handles HTML entities, Unicode normalization, and removes special whitespace characters.
    Returns a cleaned plain text string.
    """
    if not text:
        return text
    
    text = html.unescape(text)
    text = unicodedata.normalize('NFKD', text)
    text = text.replace('\xa0', ' ')  # 不间断空格
    text = text.replace('\u2009', ' ')  # 细空格
    text = text.replace('\u200b', '')  # 零宽空格
    
    return text.strip()


def parse_document_html_bs(document_html):
    """
    Parse Quip document HTML into a BeautifulSoup object.
    Adds root HTML tags to the content and creates a parseable BeautifulSoup instance
    for subsequent HTML element searching and content extraction.
    """
    document_html = "<html>" + document_html+ "</html>"
    return BeautifulSoup(document_html, "html.parser")



@mcp.tool()
def get_thread_metadata(thread_id):
    """Get metadata of a quip thread including its id, type, title, link, people who have access to the thread and their access levels by specifying the thread id..
    
    Args:
        thread_id: an unique id of a thread in quip, used to access a quip thread. For example, if a url of a quip thread is https://quip-amazon.com/AbcCFHsxcstk/AgentTest, then the thread id is AbcCFHsxcstk.
    
    Returns:
        String of a python dict, containing the metadata of a quip thread including id, type, title, link, and accessible people with their access levels.
    """
    try:
        # Get thread data
        client = init_quip_client()
        response = client.get_thread(thread_id)
        thread = response["thread"]
        thread_access = []
        for uid, level in response["access_levels"].items():
            user = client.get_user(uid)
            thread_access.append({
                "name": user["name"],
                "email": user["emails"][0],
                "id": uid,
                "access_level": level["access_level"]
            })
        meta_data = {
            "thread_id": thread["id"], 
            "thread_type": thread["type"],
            "thread_title": thread["title"],
            "thread_link": thread["link"],
            "thread_access": thread_access
            }
        return json.dumps(meta_data)
    except Exception as e:
        raise


@mcp.tool()
def get_thread_content(thread_id):
    """Get content of a quip thread by specifying the thread id.
    
    Args:
        thread_id: an unique id of a thread in quip, used to access a quip thread. For example, if a url of a quip thread is https://quip-amazon.com/AbcCFHsxcstk/AgentTest, then the thread id is AbcCFHsxcstk.
        
    Returns:
        Content of the quip thread.
    """
    return get_document_content(thread_id)


@mcp.tool()
def get_user_ids_by_emails(user_list):
    """Given emails of a group of users, get User IDs for these specified users. 
    
    Args:
        user_list: A list containing one or multiple user emails. E.g. ["xxx@abc.com", "yyy@abc.com"]
    
    Returns:
        IDs of requested users.
    """    
    try:
        client = init_quip_client()
        user_profiles = client.get_users(user_list)
        ids = {}
        for u in user_list:
            id_tmp = user_profiles[u]["id"]
            ids[f"User {u} ID"] = id_tmp
        return json.dumps(ids)
    except Exception as e:
        raise


@mcp.tool()
def add_members_to_thread_with_access_level(thread_id, members_with_access_level):
    """Add access permissions to a thread to specified members, according to the specified access levels.
    
    Args:
        thread_id: an unique id of a thread in quip, used to access a quip thread. For example, if a url of a quip thread is https://quip-amazon.com/AbcCFHsxcstk/AgentTest, then the thread id is AbcCFHsxcstk.
        members_with_access_level: A python dictionary containing member IDs within different access levels. Format: [{"access_level": 1, "member_ids": ["BBBBBBBB"]}, {"access_level": 2, "member_ids": ["AAAAAAAA"]}]. Specifically, 0: Full access, 1: Edit, 2: Comment, 3: View.

    Returns:
        A message showing the operation result.
    """    
    try:
        client = init_quip_client()
        client.add_thread_members_by_access_level(thread_id, members_with_access_level)
        users = []
        [users.extend(u["member_ids"]) for u in members_with_access_level]
        return f"Permissions added for {", ".join([get_username_by_id(u) for u in users])}."
    except Exception as e:
        raise


@mcp.tool()
def remove_members_access_from_thread(thread_id, members_to_remove):
    """Remove specified members' access to a thread.
    
    Args:
        thread_id: an unique id of a thread in quip, used to access a quip thread. For example, if a url of a quip thread is https://quip-amazon.com/AbcCFHsxcstk/AgentTest, then the thread id is AbcCFHsxcstk.
        members_to_remove: A list of user IDs whose access to the specified thread are to be removed. E.g. ["AAAAAAAAAA", "BBBBBBBBB"]
    
    Returns:
        A message showing the operation result.
    """    
    try:
        client = init_quip_client()
        client.remove_thread_members(thread_id, members_to_remove)
        return f"Permissions for {", ".join([get_username_by_id(u) for u in members_to_remove])} removed."
    except Exception as e:
        raise


@mcp.tool()
def get_comments_from_thread(thread_id):
    """Retrieve up to 100 comments from a specified Quip thread. 
    
    Args:
        thread_id: an unique id of a thread in Quip, used to access a quip thread. For example, if a url of a quip thread is https://quip-amazon.com/AbcCFHsxcstk/AgentTest, then the thread id is AbcCFHsxcstk.
 
    Returns:
        Details of comments are returned, including reviewer, content and reference of the comment, recreation time of the comment for each comment.
    """ 
    try:
        client = init_quip_client()
        raw_comments = client.get_messages(thread_id, count=100)
        document_html = client.get_thread(thread_id).get("html")
        results = []
        for comm in raw_comments:
            if comm.get("visible"):
                if comm.get("annotation"):
                    if comm.get("annotation").get("highlight_section_ids"):
                        section = get_section_bs(comm.get("annotation").get("highlight_section_ids")[0], thread_id=thread_id, document_html=document_html)
                        if section is not None:
                            if "img" in section.name:
                                reference = section.get("alt")
                            else:
                                reference = clean_extracted_text(section.text) if section.text else None
                        else:
                            reference = None
                    elif comm.get("annotation").get("id"):
                        section = get_section_bs(comm.get("annotation").get("id"), thread_id=thread_id, document_html=document_html)
                        reference = clean_extracted_text(section.text) if section.text is not None else None
                else:
                    reference = None
                results.append({
                    "reviewer": comm.get("author_name"),
                    "comment_content": comm.get("text"),
                    "comment_on": reference,
                    "created:": datetime.datetime.fromtimestamp(comm.get("created_usec") / 1e6).ctime(),
                    "last_updated": datetime.datetime.fromtimestamp(comm.get("updated_usec") / 1e6).ctime()
                })
    except Exception as e:
        raise e
    return json.dumps(results, ensure_ascii=False)


if __name__ == "__main__":
    mcp.run()