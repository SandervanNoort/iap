<?php

$tfield = array();

// elementos do form
$tfield['sintomas_check'] = array('DBName'=>'q3000', 'Type'=>0, 
        'CType'=>'check_box','Text'=>'Desde a ultima vez que preencheu o questionário, sofreu algum dos seguintes sintomas?', 'Rules'=>'0:12;14:12', 'Page'=>1, 'Key'=>false); 

$tfield['sintomas_data_input'] = array('DBName'=>'q3001', 'Type'=>1, 
        'CType'=>'select_list','Text'=>'Quando deu pelo início dos sintomas?', 'Rules'=>'', 'Page'=>2, 'Key'=>false);

$tfield['temp_radio'] = array('DBName'=>'q3002', 'Type'=>0, 
        'CType'=>'radio_btn','Text'=>'Mediu a temperatura? Se sim, qual foi o valor mais alto?', 'Rules'=>'1,2,3,7:6', 'Page'=>3, 'Key'=>false);

$tfield['38_data_input'] = array('DBName'=>'q3003', 'Type'=>1, 
        'CType'=>'select_list','Text'=>'Em que dia ultrapassou os 38 graus pela primeira vez?', 'Rules'=>'', 'Page'=>4, 'Key'=>false);

$tfield['febre_radio'] = array('DBName'=>'q3004', 'Type'=>0, 
        'CType'=>'radio_btn','Text'=>'A febre começou de repente?', 'Rules'=>'', 'Page'=>5, 'Key'=>false);

$tfield['medico_radio'] = array('DBName'=>'q3005', 'Type'=>0, 
        'CType'=>'radio_btn','Text'=>'Foi ao médico?', 'Rules'=>'2:8', 'Page'=>6, 'Key'=>false);

$tfield['diag_textarea'] = array('DBName'=>'q3006', 'Type'=>0, 
        'CType'=>'text_box','Text'=>'Qual foi o diagnóstico?', 'Rules'=>'', 'Page'=>7, 'Key'=>false);

$tfield['rotina_radio'] = array('DBName'=>'q3007', 'Type'=>0, 
        'CType'=>'radio_btn','Text'=>'Teve de alterar a sua rotina diária?', 'Rules'=>'2,3:10;back=all:5', 'Page'=>8, 'Key'=>false);

$tfield['casa_radio'] = array('DBName'=>'q3008', 'Type'=>0, 
        'CType'=>'radio_btn','Text'=>'Quantos dias ficou em casa?', 'Rules'=>'', 'Page'=>9, 'Key'=>false); 

$tfield['medica_check'] = array('DBName'=>'q3009', 'Type'=>0, 
        'CType'=>'check_box','Text'=>'Tomou algum dos seguintes tipos de medicamentos?', 'Rules'=>'0,6:12', 'Page'=>10, 'Key'=>false);         

$tfield['viral_data_input'] = array('DBName'=>'q3010', 'Type'=>1, 
        'CType'=>'select_list','Text'=>'Em que dia começou a tomar o medicamento?', 'Rules'=>'', 'Page'=>11, 'Key'=>false);

?>
