<?php 

$end = "end";

// elementos do form
$tfield['sintomas_check'] = array('DBName'=>'q5000', 'Type'=>0,'CType'=>'check_box','Text'=>'Desde a ultima vez que preencheu o questionário, sofreu algum dos seguintes sintomas?', 'Rules'=>"99:$end", 'Page'=>1, 'Key'=>false); 

$tfield['sintomas_data_input'] = array('DBName'=>'q5001', 'Type'=>1,'CType'=>'select_list','Text'=>'Quando deu pelo início dos sintomas?', 'Rules'=>';back=all:1', 'Page'=>2, 'Key'=>false);

$tfield['temp_radio'] = array('DBName'=>'q5002', 'Type'=>0,'CType'=>'radio_btn','Text'=>'Teve febre?', 'Rules'=>'99:6;back=all:2', 'Page'=>3, 'Key'=>false);

$tfield['38_data_input'] = array('DBName'=>'q5003', 'Type'=>1,'CType'=>'select_list','Text'=>'Quando começou a febre?', 'Rules'=>';back=all:3', 'Page'=>4, 'Key'=>false);

$tfield['febre_radio'] = array('DBName'=>'q5004', 'Type'=>0,'CType'=>'radio_btn','Text'=>'A febre começou de repente?', 'Rules'=>';back=all:4', 'Page'=>5, 'Key'=>false);

$tfield['medico_radio'] = array('DBName'=>'q5005', 'Type'=>0,'CType'=>'radio_btn','Text'=>'Foi ao médico?', 'Rules'=>';back=all:5', 'Page'=>6, 'Key'=>false);

$tfield['rotina_radio'] = array('DBName'=>'q5006', 'Type'=>0,'CType'=>'radio_btn','Text'=>'Teve de alterar a sua rotina diária?', 'Rules'=>"99:$end;back=all:6", 'Page'=>7, 'Key'=>false);

$tfield['casa_radio'] = array('DBName'=>'q5007', 'Type'=>0,'CType'=>'radio_btn','Text'=>'Quantos dias alterou a sua rotina?', 'Rules'=>';back=all:7', 'Page'=>8, 'Key'=>false); 

?>
