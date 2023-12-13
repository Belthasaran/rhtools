<?php
header("Content-Type: text/plain");
#$qstring = $_SERVER['QUERY_STRING'];
#$qstring = 'invictus';
$qstring = $_GET['q'];
$qstring = preg_replace('/[^a-zA-Z0-9 ]/', '_', ($qstring));

#echo "[] qstring = [$qstring\n]";
$rh = file_get_contents("smwhacks.json");
$rh2 = file_get_contents("smwdb.json");
$jso = json_decode($rh,true);
$foundEnt = null;
$hacknames = '';

foreach(json_decode($rh2, true) as &$entry)
{
	array_push($jso, $entry);
}

foreach($jso as &$entry)
{
        if (  preg_match('/\b' . $qstring . '\b/i', $entry["authors"] )) {
                if ($hacknames != '') {
                        $hacknames .= '; ';
                } else {
                        $hacknames .= 'By ' . $qstring . ': ';
         }
                $hacknames .= $entry["id"] . ' - ' . $entry["name"];
        }


}

if ($hacknames == '') {
foreach($jso as &$entry) 
{
	$nameval = ":" . $entry["name"] . ":";
#	echo $nameval . "\n";
#  
#
        if (strlen($qstring) < 2) { break; }

	if (str_contains($nameval, ":" .  $qstring . ":")) {
		$foundEnt = $entry;
		break;
	}

	if ($qstring == $entry["id"] ||  preg_match('/\b' . $qstring . '\b/i', $entry["name"] )) {
		$foundEnt = $entry;
		break;
	}

	if (preg_match('/\b' . $qstring . '\b/i', $entry["authors"] )) {
		if ($hacknames != '') {
			$hacknames .= '; ';
		} else {
			$hacknames .= 'By ' . $qstring . ': ';
	 }
		$hacknames .= $entry["name"];
        }

}}

if ($foundEnt) {
	   $extras = '(';
	 foreach($foundEnt["name_extra"] as &$ss) {
		  $extras .= $ss;
	 }
	   $extras .= ')';
	   echo $foundEnt["id"] . '. ' . $foundEnt["name"] . " by " . $foundEnt["authors"] . " - " . $foundEnt["length"] . " - " . $foundEnt["type"] . " - " . $extras . " - https://www.smwcentral.net" . $foundEnt["detailslink"] . "\n";
} else if ($hacknames != '') {
	echo "". $hacknames . "\n";
} else {
	echo "Could not find a game by that name";
}

#echo var_dump($foundEnt,true);

#var_dump($jso[0]["id"]);
?>
