#Handle symlink path
function getLink($fn) {
	$do=$PWD; $t=$fn; do {
		cd (Split-Path -Parent $fn); cd (Split-Path -Parent $t)
		$fn=(Split-Path -Leaf $t)
	} while($t=(Get-Item $fn).Target)
	$fn=Join-Path $PWD $fn; cd $do; $fn
}
cd (Split-Path -Parent (getLink($PSCommandPath)))
python stream.py $args