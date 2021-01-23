#!bin/sh
indent=""
arg=$1

rm -rf repos
mkdir -p repos
mkdir -p ../addons

download() {
	while read url; do
		name=$(basename ${url%.git})
		destination="repos/$name"
		echo "$indent[$name] from $url"
		git clone -q $url $destination
		cd ../addons
		addons=../package_manager/repos/$name/addons
		for addon in "$addons"/*; do
			rm -rf "$(basename "$addon")"
			if [ "$arg" = "--symlinks" ]; then
				ln -sr "$addons/$(basename "$addon")" .
			else
				cp -r "$addons/$(basename "$addon")" .
			fi
		done
		cd ../package_manager
		if [ -e "$destination/.godotmodules" ]; then
			indent=$indent\t
			download "$destination/.godotmodules"
			indent=$(echo $indent | sed "s/^.//")
		fi
	done < $1
}
download ../.godotmodules

if [ "$1" != "--symlinks" ]; then
	rm -rf repos
fi
