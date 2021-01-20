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
		echo "${indent}[$name] from $url"
		git clone -q $url $destination
		cd ../addons
		for addon in ../package_manager/repos/${name}/addons/*; do
			rm -rf "$(basename "$addon")"
			if [ "$arg" = "--symlinks" ]; then
				ln -sr ../package_manager/repos/${name}/addons/* .
			else
				cp -r "../package_manager/repos/${name}/addons/$(basename "$addon")" .
			fi
		done
		cd ../package_manager
		if [ -e "$destination/.godotmodules" ]; then
			indent="${indent}\t"
			download "${destination}/.godotmodules"
			indent=$(echo $indent | sed "s/^.//")
		fi
	done < $1
}
download ../.godotmodules

if [ "$1" != "--symlinks" ]; then
	rm -rf repos
fi
