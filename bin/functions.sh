#! /bin/sh

mkemptydir () {
	rm -rf "$1"
	mkdir -p "$1"
}

confirm () {
	printf ' [yN] '
	read yesno
	yesno="$(printf %s "$yesno" | tr A-Z a-z)"
	case $yesno in
		y|yes)
			return 0
			;;
		*)
			return 1
			;;
	esac
}

get_notify_addresses () {
	[ -e "$CDIMAGE_ROOT/etc/notify-addresses" ] || return
	while read project addresses; do
		if [ "$project" = ALL ]; then
			echo "$addresses"
		elif [ "$project" = "$1" ]; then
			echo "$addresses"
		fi
	done < "$CDIMAGE_ROOT/etc/notify-addresses"
}
