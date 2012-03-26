# -*- tcl -*-
# this creates a proxy for a tk text widget so that I can intercept
# the low level commands that modify the text (ie: insert, delete and
# replace). When it detects those commands it will call the passed-in
# function (post_change_hook) I can't use a virtual event because
# tkinter doesn't pass the -data option through to the bound command
CREATE_WIDGET_PROXY = '''
proc widget_proxy {actual_widget post_change_hook args} {

    # "flag" contains the name of another variable; it is
    # used in the final block of code in this proc
    set flag ::dont_recurse(actual_widget)

    if {! [info exists $flag]} {
	# need to save canonical form of indices, since 
	# after the text is change the symbolic indices 
	# will have changed too
	set command [lindex $args 0]
	if {$command in {insert delete replace}} {
	    set index1 [$actual_widget index [lindex $args 1]]
	    $actual_widget mark set start_change $index1
	    $actual_widget mark set end_change $index1
	} else {
	    $actual_widget mark set start_change insert
	    $actual_widget mark set end_change insert
	}
	$actual_widget mark gravity start_change left
	$actual_widget mark gravity end_change right

	if {$command == "insert"} {
	    set index1 [$actual_widget index [lindex $args 1]]
	    set args [lreplace $args 1 1 $index1]

	} elseif {$command == "replace"} {
	    set index1 [$actual_widget index [lindex $args 1]]
	    set index2 [$actual_widget index [lindex $args 2]]
	    set args [lreplace $args 1 2 $index1 $index2]

	} elseif {$command == "delete"} {
	    set index1 [$actual_widget index [lindex $args 1]]
	    if {[llength $args] == 2} {
		set args [list "delete" $index1]
	    } else {
		set index2 [$actual_widget index [lindex $args 2]]
		set args [list "delete" $index1 $index2]
	    }
	}
    }

    set result [uplevel [linsert $args 0 $actual_widget]]

    if {! [info exists $flag]} {
	if {([lindex $args 0] in {insert replace delete}) ||
	    ([lrange $args 0 2] == {mark set insert})} {
	    # the flag makes sure that whatever happens in the
	    # callback doesn't cause the callbacks to be called again.
	    set $flag 1
	    catch {$post_change_hook $result {*}$args } result
	    unset -nocomplain $flag
	}
    }
    return $result
}
'''


