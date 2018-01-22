find . -type f -name *.pyc | while read f
do
	git rm "$f"
	rm "$f"
done

find . -type f -name *.py~ | while read f
do
	git rm "$f"
	rm "$f"
done

git rm *.py~
git rm *.txt~
git rm *.pyc
rm *.pyc
rm *.py~
rm *.txt~
rm *.md~
rm *.sh~
rm -rvf build
rm -rvf pycosworth
