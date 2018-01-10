<?php

// $basePath 	= dirname( __FILE__ );
// 
// global $dengueCrit;
// //Avaliação Dengue na web: Você pode estar com dengue. Procure, "imediatamente", um atendimento médico! (Boneco Roxo)
// $dengueCrit[0] = 'q2000:1'; //Febre
// $dengueCrit[1] = 'q3011:4,5';
// $dengueCrit[2] = 'q3000:01,03';
// 
// global $influCrit;
// //Avaliação Dengue na web: Você pode estar com dengue. Procure um atendimento médico! (Boneco Vermelho)
// $influCrit[0]  = 'q2000:1'; //Febre
// $influCrit[1]  = 'q3000:02,03,04,05,06,07,08,09,10,11,12'; //Escondo 01
// $influCrit[2]  = 'q3000:01,03,04,05,06,07,08,09,10,11,12'; //Escondo 02
// $influCrit[3]  = 'q3000:01,02,04,05,06,07,08,09,10,11,12'; //Escondo 03
// $influCrit[4]  = 'q3000:01,02,03,05,06,07,08,09,10,11,12'; //Escondo 04
// $influCrit[5]  = 'q3000:01,02,03,04,06,07,08,09,10,11,12'; //Escondo 05
// $influCrit[6]  = 'q3000:01,02,03,04,05,07,08,09,10,11,12'; //Escondo 06
// $influCrit[7]  = 'q3000:01,02,03,04,05,06,08,09,10,11,12'; //Escondo 07
// $influCrit[8]  = 'q3000:01,02,03,04,05,06,07,09,10,11,12'; //Escondo 08
// $influCrit[9]  = 'q3000:01,02,03,04,05,06,07,08,10,11,12'; //Escondo 09
// $influCrit[10] = 'q3000:01,02,03,04,05,06,07,08,09,11,12'; //Escondo 10
// $influCrit[11] = 'q3000:01,02,03,04,05,06,07,08,09,10,12'; //Escondo 11
// $influCrit[12] = 'q3000:01,02,03,04,05,06,07,08,09,10,11'; //Escondo 12
// 
// global $semiCrit;
// //Avaliação Dengue na web: Caso a febre continue, procure um atendimento médico! (Boneco Azul)
// $semiCrit[0] = 'q2000:1'; //Febre
// $semiCrit[1] = 'q3000:01,02,03,04,05,06,07,08,09,10,11,12,13';
// 
// require( $basePath . '/form.class.extends.php' );
// global $my;
// define ( '_TABLE_NAME', 'survey_answers' );

//Página 1
$tfield['tevefebre_radio'] = array('DBName'=>'q2000', 'Type'=>0, 'CType'=>'radio_btn', 'Text'=>'Você teve febre nos últimos 7 (sete) dias?', 'Rules'=>'0:5', 'Page'=>1, 'Key'=>false);

//Página 2
$tfield['sintomas_data_input'] = array('DBName'=>'q3001', 'Type'=>0, 'CType'=>'select_list', 'Text'=>'Qual a data de início da febre?', 'Rules'=>'', 'Page'=>2, 'Key'=>false);

$tfield['temp_radio'] = array('DBName'=>'q3002', 'Type'=>0, 'CType'=>'radio_btn', 'Text'=>'Qual a temperatura da febre?', 'Rules'=>'', 'Page'=>2, 'Key'=>false);

$tfield['febre_radio'] = array('DBName'=>'q3004', 'Type'=>0, 'CType'=>'radio_btn','Text'=>'A febre começou de repente?', 'Rules'=>'', 'Page'=>2, 'Key'=>false);

$tfield['duracao_radio'] = array('DBName'=>'q3011', 'Type'=>0, 'CType'=>'radio_btn','Text'=>'Qual a duração da febre?', 'Rules'=>'', 'Page'=>2, 'Key'=>false);

//Página 3
$tfield['sintomas_check'] = array('DBName'=>'q3000', 'Type'=>0, 'CType'=>'check_box', 'Text'=>'Na última semana apresentou algum desses sintomas?', 'Rules'=>'', 'Page'=>3, 'Key'=>false); 

//Página 4
$tfield['medico_radio'] = array('DBName'=>'q3005', 'Type'=>0, 'CType'=>'radio_btn','Text'=>'Foi atendido por um médico?', 'Rules'=>'', 'Page'=>4, 'Key'=>false);

$tfield['rotina_radio'] = array('DBName'=>'q3007', 'Type'=>0, 'CType'=>'radio_btn','Text'=>'Deixou de realizar as atividades diárias?', 'Rules'=>'', 'Page'=>4, 'Key'=>false);

//Página 5
$tfield['pessoafebre_radio'] = array('DBName'=>'q3012', 'Type'=>0, 'CType'=>'radio_btn', 'Text'=>'Há outras pessoas em sua casa com febre?', 'Rules'=>'', 'Page'=>5, 'Key'=>false);

$tfield['encontrou_radio'] = array('DBName'=>'q3013', 'Type'=>0, 'CType'=>'radio_btn', 'Text'=>'Encontrou em sua residência ou local de trabalho o mosquito da dengue (Aedes aegypti)?', 'Rules'=>'', 'Page'=>5, 'Key'=>false);


// $sintomas = new survey("Questionário de Sintomas", _TABLE_NAME, 5, "user_active", "influenza_positive", "influenza_semi_positive", "table_profile_answers");
// foreach (array_keys($tfield) as $key)
//   $sintomas->add($key, $tfield[$key]['DBName'], $tfield[$key]['Type'], '', $tfield[$key]['Text'], $tfield[$key]['CType'], $tfield[$key]['Rules'], $tfield[$key]['Page'], $tfield[$key]['Key']);
// $sintomas->add("data", "date", 1, date("Y-m-d"), '', '', '', 0, true);
// $sintomas->add("id", "uid", 2, $my->id, '', '', '', 0, true);
// 
?>
