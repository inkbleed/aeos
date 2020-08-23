import custom

run (.+):
    hotkey win r
    wait 5 seconds for run dialog
    type $0
    press enter

open chrome:
    if chrome app is not visible:
        click on chrome icon
    wait 5 seconds for chrome app
    if chrome app is not visible:
        say unable to open chrome

new tab:
    open chrome
    hotkey command t

focus url bar:
    open chrome
    hotkey command l
    
open firefox:
    if firefox heading is visible:
        click on firefox heading
        wait 1
        press esc
        wait 1
    if firefox heading is not visible:
        click on firefox icon
    wait 30 seconds for firefox heading
    say Firefox is opened!

close firefox:
    if firefox heading is visible:
        click on firefox heading
        wait 1
        press esc
        wait 1
    if firefox heading is not visible:
        click on firefox icon
    wait 3
    if firefox heading is visible:
        hotkey alt f4
        
open new tab:
    open firefox
    hotkey ctrl t   
    
go to gmail:
    if google gmail icon is visible:
        click on google gmail icon
        wait 1
        press esc
        wait 1
        click on gmail inbox link
    
    if google gmail icon is not visible:
        open firefox
        open new tab
        click on url bar
        type https://www.gmail.com
        press enter
        
go to the pirate bay:
    open firefox
    open new tab
    click on url bar
    type http://www.thepiratebay.org
    press enter

torrent (.+):
    go to the pirate bay
    wait 30
    if the pirate bay logo is not visible:
        press f5
    wait 120 seconds for the pirate bay logo
    type $0
    press enter
    wait 120 seconds for the pirate bay search results
    hotkey ctrl f
    wait 1
    type $0
    press enter
    wait 1
    press enter
    wait 1
    press esc
    wait 1
    press enter
    click on magnet link
    wait 60 seconds for utorrent add new torrent heading
    click on ok button

log in to gmail as Aeos:
    go to gmail
    wait 30 seconds for gmail account icon OR Aeos Prime gmail account link
    if Aeos Prime gmail account link is not visible:
        click on gmail account icon
        wait 1
        if Aeos Prime logged in to gmail is not visible:
            click on gmail sign out button
            wait 30 seconds for Aeos Prime gmail account link
        if Aeos Prime logged in to gmail is visible:
            press esc
    if Aeos Prime gmail account link is visible:
        click on Aeos Prime gmail account link
        click on gmail sign in button
    if gmail account icon is visible:
        click on gmail account icon
        if Aeos Prime logged in to gmail is visible:
            press esc
            wait 1
        if Aeos Prime gmail account link is visible:
            click on Aeos Prime gmail account link
        

get status of open Aeos instance:
    set aeos_status = Not sure if it worked or not
    if windows command line is not visible:
        click on windows command line icon
        wait 2
    if windows command line is visible:
        say Checking status of task I just triggered...
        set req_confidence = 0.9
        if Aeos task complete text is visible:
            set aeos_status = Task Complete!
        if Aeos could not complete text is visible:
            set aeos_status = Didn't complete properly
        if Aeos task complete text is not visible:
            set aeos_status = Didn't complete properly
    set req_confidence = $DEFAULT_CONFIDENCE
    say The status of the other Aeos instance is: $AEOS_STATUS
	
close open Aeos instance:
    say closing the open Aeos instance
    if windows command line is not visible:
        click on windows command line icon
    if windows command line is visible:
        click on windows command line
        wait 1
        press enter
        wait 1
        type quit
        press enter
        wait 1
        type exit
        press enter

close open gmail tabs:
    say closing any open gmail tabs
    open firefox
    wait 2
    repeat 3 times:
        wait 2
        if gmail tab is visible:
            click on gmail tab
            wait 2
            hotkey ctrl w
        if gmail tab is not visible:
        
reply with temporary task results:
    log in to gmail as Aeos
    click on gmail inbox link
    double click on old email to Aeos
    click on gmail reply field
    wait 10 seconds for gmail send button
    type $AEOS_STATUS
    press enter
    press enter
    hotkey ctrl v
    wait 1
    press up
    wait 1
    press up
    wait 1
    press up    
    wait 20 seconds for screenshot start menu
    click on gmail send button
    click on gmail remove inbox label button
    click on gmail labels button
    click on gmail actioned label button
    click on gmail inbox link

email screenshot to (.+):
    wait 1
    press printscreen
    run firefox
    wait 60 seconds for firefox heading
    log in to gmail as Aeos
    click on gmail compose button
    wait 10 seconds for gmail send button
    type $0
    press enter
    click on gmail subject field
    type Requested screenshot
    wait 1
    press tab
    wait 1
    hotkey ctrl v
    wait 1
    press up
    wait 1
    press up
    wait 1
    press up    
    wait 120 seconds for screenshot start menu
    click on gmail send button
    wait 30 seconds for find gmail message sent notification
    close firefox

    
create temporary task from clipboard:
    run cmd
    wait 30 seconds for windows command line
    type $LOCALDRIVE:
    press enter
    type cd\
    press enter
    wait 1
    type cd Aeos
    press enter
    wait 1
    type python main.py
    press enter
    set req_confidence = 0.9
    wait 60 seconds for Aeos task complete text
    set req_confidence = $DEFAULT_CONFIDENCE
    right click on dos window
    click on paste button
    wait 240
    press printscreen
    get status of open Aeos instance
    close open Aeos instance

check your email:
    log in to gmail as Aeos
    wait 5
    say Trying to find new email
    set req_confidence = 0.9
    if new email to Aeos is visible:
        set req_confidence = $DEFAULT_CONFIDENCE
        say "Got new email!"
        click on new email to Aeos
        wait 2
        drag from open email to Aeos to gmail head icon
        hotkey ctrl c
        create temporary task from clipboard
        reply with temporary task results
    if new email to Aeos is not visible:
        say No emails!
    set req_confidence = $DEFAULT_CONFIDENCE
    
go to google drive:
    log in to gmail as Aeos
    click on google apps icon
    click on google drive icon

go to slack:
    open chrome
    if slack tab icon is visible:
        click on slack tab icon
    if slack tab icon is not visible:
        new tab
        type https://matrak-au.slack.com/
        press enter
        wait 60 seconds for slack tab icon
    if matrak slack workspace is not visible:
        if slack signin button is not visible:
            say Fuck, i'm stuck!
        if slack signin button is visible:
            click on slack signin button
            wait 60 seconds for matrak slack workspace

send (.+) a screenshot on slack:
    wait 1
    press printscreen
    go to slack
    click on $0 slack channel
    wait 1
    hotkey ctrl v
    wait 30 seconds for slack upload file dialog
    type One screenshot!
    click on slack upload button

execute sql (.+):
    sql $0
    $ $MYDIR\plugins\API_Analysis\output.html
    
idler:
    execute sql call analyseRecentUserUpdates();
    send stats a screenshot on slack
    execute sql select count(usage_log_id) Log, (date(timestamp)) logDate, username, action, campaign_id, tracking_id, prev_campaign_id, prev_tracking_id from logs_usage, users where ((tracking_id = user_id) OR (prev_tracking_id = user_id)) group by logDate, username order by usage_log_id desc limit 50;
    send stats a screenshot on slack
    execute sql call getLatestRegistrations();
    send stats a screenshot on slack