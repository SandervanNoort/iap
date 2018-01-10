<?php

$tfield = array();

// elementos do form
$tfield['sintomas_check'] = array('DBName'=>'q3000', 'Type'=>0, 
        'CType'=>'check_box','Text'=>'Dall\'ultima volta che hai compilato il questionario, hai sofferto di qualcuno di questi sintomi?', 'Rules'=>'0:14;14:14', 'Page'=>1, 'Key'=>false); 

$tfield['sintomas_data_input'] = array('DBName'=>'q3001', 'Type'=>1, 
        'CType'=>'text_box','Text'=>'Quando hanno avuto inizio i sintomi?', 'Rules'=>'', 'Page'=>2, 'Key'=>false);

$tfield['temp_radio'] = array('DBName'=>'q3002', 'Type'=>0, 
        'CType'=>'radio_btn','Text'=>'Hai avuto la febbre? Se si, qual\'è stato il valore massimo?', 'Rules'=>'1,2,3,7:6', 'Page'=>3, 'Key'=>false);

$tfield['38_data_input'] = array('DBName'=>'q3003', 'Type'=>1, 
        'CType'=>'text_box','Text'=>'Quando ha oltrepassato i 38 gradi per la prima volta?', 'Rules'=>'', 'Page'=>4, 'Key'=>false);

$tfield['febre_radio'] = array('DBName'=>'q3004', 'Type'=>0, 
        'CType'=>'radio_btn','Text'=>'La febbre è iniziata improvvisamente?', 'Rules'=>'', 'Page'=>5, 'Key'=>false);

$tfield['medico_radio'] = array('DBName'=>'q3005', 'Type'=>0, 
        'CType'=>'radio_btn','Text'=>'Hai consultato telefonicamente un medico?', 'Rules'=>'1,2,3:9', 'Page'=>6, 'Key'=>false);

$tfield['medico2_radio'] = array('DBName'=>'q30051', 'Type'=>0,
        'CType'=>'radio_btn','Text'=>'Sei stato visitato da una delle seguenti figure sanitarie?', 'Rules'=>'1,2:9;4:10', 'Page'=>7, 'Key'=>false);

$tfield['prontsocc_radio'] = array('DBName'=>'q30052', 'Type'=>0,
        'CType'=>'radio_btn','Text'=>'In Pronto Soccorso ti sei recato:', 'Rules'=>'', 'Page'=>8, 'Key'=>false);

$tfield['diagnosi_textarea'] = array('DBName'=>'q3006', 'Type'=>0,
        'CType'=>'text_box','Text'=>'Qual\'è stata la diagnosi?', 'Rules'=>'', 'Page'=>9, 'Key'=>false);

$tfield['rotina_radio'] = array('DBName'=>'q3007', 'Type'=>0, 
        'CType'=>'radio_btn','Text'=>'Hai dovuto modificare la tua routine quotidiana?', 'Rules'=>'2,3:12;back=all:5', 'Page'=>10, 'Key'=>false);

$tfield['casa_radio'] = array('DBName'=>'q3008', 'Type'=>0, 
        'CType'=>'radio_btn','Text'=>'Per quanti giorni sei rimasto a casa?', 'Rules'=>'', 'Page'=>11, 'Key'=>false); 

$tfield['medica_check'] = array('DBName'=>'q3009', 'Type'=>0, 
        'CType'=>'check_box','Text'=>'Hai assunto qualcuno dei seguenti tipi di farmaci?', 'Rules'=>'6:14', 'Page'=>12, 'Key'=>false);         

$tfield['viral_data_input'] = array('DBName'=>'q3010', 'Type'=>1, 
        'CType'=>'text_box','Text'=>'Quando hai iniziato l\'assunzione degli antivirali?', 'Rules'=>'', 'Page'=>13, 'Key'=>false);                 

$tfield['diag_textarea'] = array('DBName'=>'q3011', 'Type'=>0,
        'CType'=>'text_box','Text'=>'Come ti senti oggi??', 'Rules'=>'', 'Page'=>14, 'Key'=>false);

?>
