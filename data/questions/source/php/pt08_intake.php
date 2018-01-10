<?php 

$end = "end";

// elementos do form
$tfield['accept_study_check'] = array('DBName'=>'q2010', 'Type'=>0, 'CType'=>'check_box','Text'=>'Aceita participar em quais dos seguintes estudos?', 'Rules'=>'', 'Page'=>1, 'Key'=>false);

//--------

$tfield['participationtype_1'] = array('DBName'=>'q2013', 'Type'=>0, 'CType'=>'radio_btn','Text'=>'Tipo de Participação', 'Rules'=>'1:7;2:3;3:5;4:22', 'Page'=>2, 'Key'=>false);

$tfield['participation2_evora'] = array('DBName'=>'q2014', 'Type'=>0, 'CType'=>'radio_btn','Text'=>'Tipo de Participação (Universidade de Évora)', 'Rules'=>'', 'Page'=>3, 'Key'=>false);
$tfield['participation3_evora'] = array('DBName'=>'q2015', 'Type'=>0, 'CType'=>'check_box','Text'=>'Localização (Universidade de Évora)', 'Rules'=>'all:7', 'Page'=>4, 'Key'=>false);

$tfield['participation2_porto'] = array('DBName'=>'q2014', 'Type'=>0, 'CType'=>'radio_btn','Text'=>'Tipo de Participação (Universidade do Porto)', 'Rules'=>'', 'Page'=>5, 'Key'=>false);
$tfield['participation3_porto'] = array('DBName'=>'q2015', 'Type'=>0, 'CType'=>'check_box','Text'=>'Localização (Universidade do Porto)', 'Rules'=>'', 'Page'=>6, 'Key'=>false);  

$tfield['participation2_pt'] = array('DBName'=>'q2016', 'Type'=>0, 'CType'=>'radio_btn','Text'=>'Tipo de Participação (PT)', 'Rules'=>'all:7', 'Page'=>22, 'Key'=>false);

//--------
 
$tfield['sexo_radio'] = array('DBName'=>'q1001', 'Type'=>0, 'CType'=>'radio_btn', 'Text'=>'Sexo', 'Rules'=>'all:9', 'Page'=>7, 'Key'=>false);
$tfield['data_nasc_input'] = array('DBName'=>'q1002','Type'=>1, 'CType'=>'select_list', 'Text'=>'Data de Nascimento', 'Rules'=>'all:9', 'Page'=>7, 'Key'=>false); 

// $tfield['country_list'] = array('DBName'=>'q1003','Type'=>1, 'CType'=>'select_list', 'Text'=>'Nacionalidade', 'Rules'=>'', 'Page'=>8, 'Key'=>false);

$tfield['cod_postal_list'] = array('DBName'=>'q1000', 'Type'=>0, 'CType'=>'select_list','Text'=>'Código Postal de Residência', 'Rules'=>'all:11', 'Page'=>9, 'Key'=>false);
$tfield['cod_postal_list_work'] = array('DBName'=>'q1005', 'Type'=>0, 'CType'=>'select_list','Text'=>'Código Postal de Trabalho/Escola', 'Rules'=>'all:11', 'Page'=>9, 'Key'=>false);

// $tfield['esc_list'] = array('DBName'=>'q1004','Type'=>1, 'CType'=>'select_list', 'Text'=>'Escolaridade', 'Rules'=>'', 'Page'=>10, 'Key'=>false);

$tfield['ocup_list'] = array('DBName'=>'q2000','Type'=>0, 'CType'=>'select_list', 'Text'=>'Qual a sua ocupação diária?', 'Rules'=>'', 'Page'=>11, 'Key'=>false); 

$tfield['meio_transp_check'] = array('DBName'=>'q2001','Type'=>0, 'CType'=>'check_box', 'Text'=>'Que meio de transporte utiliza diáriamente?', 'Rules'=>'', 'Page'=>12, 'Key'=>false);

$tfield['const_ano_radio'] = array('DBName'=>'q2002','Type'=>0, 'CType'=>'radio_btn', 'Text'=>'Em média, quantas constipações sofre por ano?', 'Rules'=>'', 'Page'=>13, 'Key'=>false);

$tfield['vacina_grip_radio'] = array('DBName'=>'q2040','Type'=>0, 'CType'=>'radio_btn', 'Text'=>'Tomou a vacina da gripe (injecção) este ano?', 'Rules'=>'99:23', 'Page'=>14, 'Key'=>false);

$tfield['vacina_sim_pq'] = array('DBName'=>'q2041','Type'=>0, 'CType'=>'check_box', 'Text'=>'Porque razão tomou a vacina?', 'Rules'=>'', 'Page'=>15, 'Key'=>false);

$tfield['vacina_nao_pq'] = array('DBName'=>'q2042','Type'=>0, 'CType'=>'check_box', 'Text'=>'Porque razão não tomou a vacina?', 'Rules'=>'all:16', 'Page'=>23, 'Key'=>false);

$tfield['sofre_doencas_radio'] = array('DBName'=>'q2004','Type'=>0, 'CType'=>'radio_btn', 'Text'=>'Sofre de alguma das seguintes doenças?', 'Rules'=>'', 'Page'=>16, 'Key'=>false);

$tfield['e_fumador_radio'] = array('DBName'=>'q2005','Type'=>0, 'CType'=>'radio_btn', 'Text'=>'É fumador(a)?', 'Rules'=>'', 'Page'=>17, 'Key'=>false);

$tfield['desporto_radio'] = array('DBName'=>'q2008','Type'=>0, 'CType'=>'radio_btn', 'Text'=>'Com que frequência pratica desporto?', 'Rules'=>'', 'Page'=>18, 'Key'=>false);

$tfield['animais_check'] = array('DBName'=>'q2011','Type'=>0, 'CType'=>'check_box', 'Text'=>'Tem animais de estimação?', 'Rules'=>'', 'Page'=>19, 'Key'=>false);


//-------------------

$tfield['ag_members_list'] = array('DBName'=>'q2007','Type'=>0, 'CType'=>'select_list', 'Text'=>'Quantos membros tem o seu agregado familiar?', 'Rules'=>'0:99', 'Page'=>20, 'Key'=>false);


$tfield['_idd_ocup_list'] = array('DBName'=>'q2006','Type'=>0, 'CType'=>'select_list', 'Text'=>'Por favor caracterize cada um dos membros (trabalha/escola)', 'Rules'=>'all:99', 'Page'=>21, 'Key'=>false);
$tfield['_idd_list'] = array('DBName'=>'q2003','Type'=>0, 'CType'=>'select_list', 'Text'=>'Por favor caracterize cada um dos membros (idades)', 'Rules'=>'all:99', 'Page'=>21, 'Key'=>false);

?>
