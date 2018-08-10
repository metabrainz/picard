VERSION="2.0.3"
# comment out this line after editing following variables
echo "Update the version variable to the latest release and re-run this script after commenting this statement"; exit 1
wget -O "MusicBrainz-Picard-$VERSION.dmg" "https://github.com/metabrainz/picard/releases/download/release-$VERSION/MusicBrainz.Picard.$VERSION.dmg"
md5sum "MusicBrainz-Picard-$VERSION.dmg" > "MusicBrainz-Picard-$VERSION.dmg.md5"
wget "https://github.com/metabrainz/picard/releases/download/release-$VERSION/picard-setup-$VERSION.exe"
md5sum "picard-setup-$VERSION.exe" > "picard-setup-$VERSION.exe.md5"
wget -O "picard-$VERSION.zip" "https://github.com/metabrainz/picard/archive/release-$VERSION.zip"
wget -O "picard-$VERSION.tar.gz" "https://github.com/metabrainz/picard/archive/release-$VERSION.tar.gz"
md5sum "picard-$VERSION.zip" > "picard-$VERSION.zip.md5"
md5sum "picard-$VERSION.tar.gz" > "picard-$VERSION.tar.gz.md5"
