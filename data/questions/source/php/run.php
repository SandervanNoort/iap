<?php

$src = "br11";


$fnames = array("{$src}_intake.php", "{$src}_survey.php", "{$src}_gastro.php");
$txtobj = fopen("{$src}.txt", "w");

// connect to db
$fobj = fopen("../../../config/local.ini", "r");
$inistring = "";
while(!feof($fobj)) {
    $line = fgets($fobj);
    if (strstr($line, "[[")) {
        break;
    }
    $inistring .= $line;
}
fclose($fobj);
$ini = parse_ini_string($inistring, True);
mysql_connect($ini["db"]["host"], $ini["db"]["user"], $ini["db"]["pass"])
    or die(error(mysql_error(), $query));
mysql_select_db ($ini["db"]["db"])
    or die ("Database is not accesible");

foreach ($fnames as $fname) {
    if (!file_exists($fname)) {
        continue;
    }
    $tfield = array();
    require($fname);

    foreach ($tfield as $key => $row) {
        $question[$key]  = $row['Text'];
        $code[$key] = $row['DBName'];
    }
    array_multisort($code, SORT_ASC, $tfield);
    
    foreach ($tfield as $key=>$field) {
        $name = $key;
        $code = $field["DBName"];
        $question = $field["Text"];

//         $query = "select max(form) as max from questions_{$src} where name='$name'";
//         $result = mysql_query($query);
//         $row = mysql_fetch_array($result);
//         $form = $row["max"];

        $query = "select data1,data2 from questions_{$src} where name='$name' order by cast(form as signed), cast(data1 as signed)";
        $result = mysql_query($query);
        fwrite($txtobj, $code . " " . $question."\n");
        $datas = array();
        while ($row = mysql_fetch_object($result)) {
            $val = chop($row->data1);
            $answer = chop($row->data2);
            if (strstr($answer, "<?php")) {
                continue;
            }
            if ($val == "" && $answer == "") {
                continue;
            }
            fwrite($txtobj, "  {$val}: {$answer}\n");
        }
        fwrite($txtobj, "\n");
    }
}
fclose($txtobj);

?>
