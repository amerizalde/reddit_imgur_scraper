import BeautifulSoup as bs
import re, praw, requests, os, glob, sys
from sys import argv

IMGUR_URL_PATTERN = re.compile(r'(http://i.imgur.com/(.*))(\?.*)?')


def downloadImage(imageUrl, localFileName):
    if "Pictures" not in os.listdir(os.getcwd()):
        os.mkdir("Pictures")
    localFileName = os.getcwd() + "/Pictures/" + localFileName
    try:
        # imgur uses images for layout grids
        # they luckily all contain 'layout' in the name
        if imageUrl.find('layout') == -1:
            response = requests.get(imageUrl)

            if response.status_code == 200:
                print "Downloading {}...".format(localFileName)
                with open(localFileName, 'wb') as f:
                    for chunk in response.iter_content(4096):
                        f.write(chunk)
                    f.close()
            else:
                print "Failed to download Image: status_code == {}".format(
                    response.status_code)
        else:
            return
    except:
        return

def process_imgur_album(submission, subreddit):
    # a very readable way to get the album id from the URL
    albumId = submission.url[len('http://imgur.com/a/'):]
    htmlSource = requests.get(submission.url).text
    soup = bs.BeautifulSoup(htmlSource)
    matches = soup("img")
    data_src = 1
    url = 1
    for match in matches:
        imageUrl = match.attrs[data_src][url]
        if imageUrl.startswith('//'):
            # if no schema is supplied in the url, prepend 'http:' to it
            # the soup is Unicode, so change to u'http:'
            imageUrl = u'http:' + imageUrl
        if '?' in imageUrl:
            # this is static based on how imgur currently builds it's pages
            # may need to be changed if imgur changes
            imageFile = imageUrl[imageUrl.rfind('/') + 1:imageUrl.rfind('?')]
        else:
            imageFile = imageUrl[imageUrl.rfind('/') + 1:]
        # this is static based on how imgur currently builds it's pages
        # may need to be changed if imgur changes
        localFileName = 'reddit_{}_{}_album_{}_imgur_{}'.format(
            subreddit, submission.id, albumId, imageFile)
        downloadImage(imageUrl, localFileName)

def process_direct_link(submission, subreddit, album="None"):
    the_complete_url = IMGUR_URL_PATTERN.search(submission.url)
    the_image_without_the_url = 2
    imgurFilename = the_complete_url.group(the_image_without_the_url)
    if '?' in imgurFilename:
        imgurFilename = imgurFilename[:imgurFilename.find('?')]
    localFileName = 'reddit_{}_{}_album_{}_imgur_{}'.format(
        subreddit, submission.id, album, imgurFilename)
    downloadImage(submission.url, localFileName)

def process_imgur_page(submission, subreddit):
    htmlSource = requests.get(submission.url).text
    soup = bs.BeautifulSoup(htmlSource)
    src = 0  # the first tuple
    url = 1  # the second element of the first tuple
    imageUrl = soup("img")[0].attrs[src][url]
    if imageUrl.startswith('//'):
        # if no schema is supplied in the url, prepend 'http:' to it
        # soup is Unicode, so change to u'http:'
        imageUrl = u'http:' + imageUrl
    imageId = imageUrl[imageUrl.rfind('/') + 1:imageUrl.rfind('.')]
    if '?' in imageUrl:
        imageFile = imageUrl[imageUrl.rfind('/') + 1:imageUrl.rfind('.')]
    else:
        imageFile = imageUrl[imageUrl.rfind('/') + 1:]

    localFileName = 'reddit_{}_{}_album_None_imgur_{}'.format(
        subreddit, submission.id, imageFile)
    downloadImage(imageUrl, localFileName)

if __name__ == "__main__":
    MIN_SCORE = 20
    LIMIT = 20
    if len(argv) < 2:
        # no command line options were sent
        print """ 
    Reddit Imgur Scraper

        This will find images from the specified subreddit and download them
        into the current directory.

        Usage:

        python|pypy {} [subreddit] [minimumscore] [number_of_results]
        """.format(argv[0])
        sys.exit()
    elif len(argv) >= 2:
        # the subreddit was specified:
        target = argv[1]
        if len(argv) >= 3:
            # minimum score was also specified
            MIN_SCORE = argv[2]
            if len(argv) >= 4:
                # limit was specified
                LIMIT = argv[3]

    r = praw.Reddit(user_agent='Reference Image Scraper 0.01 /u/diddystacks')
    # Some options
    #
    # .get_new()
    # .get_hot()
    # .get_front_page()
    # .get_controversial()
    # .get_moderators()
    # .get_rising()
    # .get_top()
    submissions = r.get_subreddit(target).get_hot(limit=LIMIT)
    for submission in submissions:
        # check for all the cases where we will skip a submission:
        if "imgur.com/" not in submission.url:
            continue
        if submission.score < MIN_SCORE:
            continue
        if len(glob.glob('reddit_{}_*'.format(submission.id))) > 0:
            continue  # we've already donwloaded files for this reddit submission
        # parsing
        if 'http://imgur.com/a/' in submission.url:
            # this is an album!
            process_imgur_album(submission, target)
        elif 'http://i.imgur.com/' in submission.url:
            # this is a direct link
            process_direct_link(submission, target)
        elif 'http://imgur.com/' in submission.url:
            # this is an Imgur page with one image
            process_imgur_page(submission, target)