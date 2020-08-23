click on (.+):
    wait 60 seconds for $0
    find $0
    click

click to the (.+) of (.+):
    wait 60 seconds for $1
    move to $0 of $1
    click

move there:
    move cursor $LOCATION_X $LOCATION_Y

click there:
    move there
    click

double click there:
    move there
    click

double click on (.+):
    wait 60 seconds for $0
    find $0
    double click

right click on (.+):
    wait 60 seconds for $0
    find $0
    right click

can you see (.+):
    if $0 is not visible:
        echo no
        stop
    echo yes
