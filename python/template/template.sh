name=$1
echo $name



#copy name to folder name
cp -r template/ $name

#rename python file
mv $name/template.py $name/$name.py

#rename internal app name to given name
sed -i "s/template/${name}/g" $name/$name.py

#dont copy over template.sh
rm -f $name/template.sh
