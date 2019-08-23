// Project: AGKVersionTest
// Created: 2019-08-12
#option_explicit

#constant VERSION	"1.0"	// Read by agkbuild

#insert "demo-off.agc"		// @@demo This is an agkbuild include tag.
#insert "steam-off.agc"		// @@steam This is an agkbuild include tag.

// show all errors
SetErrorMode(2)

// set window properties
SetWindowTitle( "AGKBuildExample" )
SetWindowSize( 1024, 768, 0 )
SetWindowAllowResize( 1 ) // allow the user to resize the window

// set display properties
SetVirtualResolution( 1024, 768 ) // doesn't have to match the window
SetOrientationAllowed( 1, 1, 1, 1 ) // allow both portrait and landscape on mobile devices
SetSyncRate( 30, 0 ) // 30fps instead of 60 to save battery
SetScissor( 0,0,0,0 ) // use the maximum available screen space, no black borders
UseNewDefaultFonts( 1 ) // since version 2.0.22 we can use nicer default fonts

InitSteam()

do
    Print("This is the " + GAME_TYPE + " Version")
    Print(ScreenFPS())
    if GetRawKeyPressed(27)
		exit
	endif
    Sync()
loop
