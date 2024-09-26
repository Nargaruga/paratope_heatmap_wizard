wizard_dir=$CONDA_PREFIX/lib/python3.9/site-packages/pymol/wizard

declare -a files=("$wizard_dir/paratope.py" "$wizard_dir/paratope_heatmap")

rm $wizard_dir/paratope.py
rm -r $wizard_dir/paratope_heatmap
rm -r $wizard_dir/weights

# Remove the menu item for the paratope wizard
openvr_wizard=$wizard_dir/openvr.py
if grep -q "\[1, 'Paratope Heatmap', 'wizard paratope'\]," "$openvr_wizard"; then
    awk '!/\[1, '\''Paratope Heatmap'\'', '\''wizard paratope'\''\],/' "$openvr_wizard" > temp_file && mv temp_file "$openvr_wizard"
fi