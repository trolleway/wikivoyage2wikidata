import pywikibot

def upload_image():
    from pywikibot.specialbots import UploadRobot

    # The file path or URL of the file to upload
    file = "imgs/Vidnoe trolleybus 24 2023-01 Rastorguevo station.jpg"

    # The name of the file on Wikimedia Commons
    filename = "Vidnoe trolleybus 24 2023-01 Rastorguevo station.jpg"

    # The description of the file
    description = """{{Information
    |Description = {{en|1=Vidnoe trolleybus 24. test upload with script created by Bing Ai}}
    |Source = {{own}}
    |Author = {{Creator:Svetlov Artem}}
    |Date = {{Taken on|2023-01-31|location=Russia}}
    |Permission =
    |other_versions =
    }}
    {{Location|lat|lon}}
    == {{int:license-header}} ==
    {{self|cc-by-sa-4.0}}
    [[Category:Trolleybuses in Vidnoe]]
    [[Category:Photographs by Artem Svetlov/Moscow]]

    """

    # The site object for Wikimedia Commons
    site = pywikibot.Site("commons", "commons")

    # The upload robot object
    bot = UploadRobot(
        [file], # A list of files to upload
        description=description, # The description of the file
        useFilename=filename, # The name of the file on Wikimedia Commons
        keepFilename=True, # Keep the filename as is
        verifyDescription=True, # Ask for verification of the description
        targetSite=site # The site object for Wikimedia Commons
    )

    # Try to run the upload robot
    try:
        bot.run()
    except Exception as e:
        # Handle API errors
        print(f"API error: {e.code}: {e.info}")

def prepare_commonsfilename(commonsfilename):
    commonsfilename = commonsfilename.strip()
    if commonsfilename.startswith('File:') == False:
        commonsfilename = 'File:' + commonsfilename
    commonsfilename = commonsfilename.replace('_',' ')
    return commonsfilename

def print_structured_data(commonsfilename):
    commonsfilename = prepare_commonsfilename(commonsfilename)
    commons_site = pywikibot.Site("commons", "commons")

    # File to test and work with


    page = pywikibot.FilePage(commons_site, commonsfilename)

    # Retrieve Wikibase data
    item = page.data_item()
    item.get()

    print ('Commons MID:', item.id) # M56723871

    for prop in item.claims:
        for statement in item.claims[prop]:
            if isinstance(statement.target, pywikibot.page._wikibase.ItemPage):
                print (prop, statement.target.id, statement.target.labels.get('en'))
            else:
                print (prop, statement.target)



def append_structured_data(commonsfilename):
    commonsfilename = prepare_commonsfilename(commonsfilename)
    commons_site = pywikibot.Site("commons", "commons")

    # File to test and work with


    page = pywikibot.FilePage(commons_site, commonsfilename)
    repo = commons_site.data_repository()

    # Retrieve Wikibase data
    item = page.data_item()
    item.get()

    print ('Commons MID:', item.id) # M56723871

    stringclaim = pywikibot.Claim(repo, u'P180') #Adding IMDb ID (P345)
    stringclaim.setTarget(4212644) #Using a string
    item.addClaim(stringclaim, summary=u'Adding string claim')

print_structured_data('Moscow_Kantemirovskaya_street_2020-09.jpg')
append_structured_data('Moscow_Kantemirovskaya_street_2020-09.jpg')