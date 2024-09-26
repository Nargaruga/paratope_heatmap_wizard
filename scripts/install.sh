prefix=$CONDA_PREFIX

if [ -z "$prefix" ]; then
    echo "Could not detect conda environment. Is conda installed?"
    exit 1
fi

if [ "$CONDA_DEFAULT_ENV" == "base" ]; then
    echo "You are currently in the base environment, you may want to create a new environment before proceeding."
    echo "Do you want to proceed anyway? (y/n)"
    read proceed
    if [ "$proceed" != "y" ]; then
        exit 1
    fi
fi

pymol_dir=$prefix/lib/python3.9/site-packages/pymol

if [ ! -d "$pymol_dir" ]; then
    echo "Could not find pymol in $pymol_dir. Is pymol installed?"
    exit 1
fi

cp paratope.py $pymol_dir/wizard/
cp -r paratope_heatmap $pymol_dir/wizard/
wget https://github.com/alchemab/parapred-pytorch/raw/refs/tags/v1.0.2/parapred/weights/parapred_pytorch.h5 -P $pymol_dir/wizard/weights/

# Edit the openvr wizard to add a menu item for the paratope wizard
openvr_wizard=$pymol_dir/wizard/openvr.py
if ! grep -q "\[1, 'Paratope Heatmap', 'wizard paratope'\]," "$openvr_wizard"; then
    sed -i "/\[2, 'Wizard Menu', ''\],/a \ \ [1, 'Paratope Heatmap', 'wizard paratope']," "$openvr_wizard"
fi
