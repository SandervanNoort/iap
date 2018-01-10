<?php

$tfield = array();

// elementos do form
$tfield['participationtype_1'] = array('DBName'=>'q2013', 'Type'=>0, 'CType'=>'radio_btn','Text'=>'Tipo de Participação', 'Rules'=>'0,99:4;1:2;2:18', 'Page'=>1, 'Key'=>false);

$tfield['participation2_porto'] = array('DBName'=>'q2014', 'Type'=>0, 'CType'=>'radio_btn','Text'=>'Tipo de Participação (Universidade do Porto)', 'Rules'=>'', 'Page'=>2, 'Key'=>false);
$tfield['participation3_porto'] = array('DBName'=>'q2015', 'Type'=>0, 'CType'=>'check_box','Text'=>'Localização (Universidade do Porto)', 'Rules'=>'', 'Page'=>3, 'Key'=>false);  

$tfield['participation2_evora'] = array('DBName'=>'q2014', 'Type'=>0, 'CType'=>'radio_btn','Text'=>'Tipo de Participação (Universidade de Évora)', 'Rules'=>'', 'Page'=>18, 'Key'=>false);
$tfield['participation3_evora'] = array('DBName'=>'q2015', 'Type'=>0, 'CType'=>'check_box','Text'=>'Localização (Universidade de Évora)', 'Rules'=>'all:4', 'Page'=>19, 'Key'=>false);



//DONT CHANGE THIS "cod_postal_list" (SEE FORM.CLASS)
  
$tfield['sexo_radio'] = array('DBName'=>'q1001', 'Type'=>0, 'CType'=>'radio_btn', 'Text'=>'Sexo', 'Rules'=>'', 'Page'=>4, 'Key'=>false);
$tfield['data_nasc_input'] = array('DBName'=>'q1002','Type'=>1, 'CType'=>'select_list', 'Text'=>'Data de Nascimento', 'Rules'=>'', 'Page'=>4, 'Key'=>false); 

$tfield['cod_postal_list'] = array('DBName'=>'q1000', 'Type'=>0, 'CType'=>'select_list','Text'=>'Código Postal de Residência', 'Rules'=>'', 'Page'=>5, 'Key'=>false);
$tfield['cod_postal_list_work'] = array('DBName'=>'q1005', 'Type'=>0, 'CType'=>'select_list','Text'=>'Código Postal de Trabalho/Escola', 'Rules'=>'', 'Page'=>5, 'Key'=>false);

$tfield['ocupa_check'] = array('DBName'=>'q2000','Type'=>0, 'CType'=>'check_box', 'Text'=>'Qual a sua ocupação diária?', 'Rules'=>'', 'Page'=>5, 'Key'=>false); 
$tfield['meio_transp_check'] = array('DBName'=>'q2001','Type'=>0, 'CType'=>'check_box', 'Text'=>'Que meio de transporte utiliza diáriamente?', 'Rules'=>'', 'Page'=>6, 'Key'=>false);
$tfield['const_ano_radio'] = array('DBName'=>'q2002','Type'=>0, 'CType'=>'radio_btn', 'Text'=>'Em média, quantas constipações sofre por ano?', 'Rules'=>'', 'Page'=>7, 'Key'=>false);

$tfield['vacina_grip_radio'] = array('DBName'=>'q2040','Type'=>0, 'CType'=>'radio_btn', 'Text'=>'Tomou a vacina da gripe (injecção) este ano?', 'Rules'=>'1:21;2:20', 'Page'=>8, 'Key'=>false);
$tfield['vacina_sim_pq'] = array('DBName'=>'q2041','Type'=>0, 'CType'=>'check_box', 'Text'=>'Porque tomou a vacina?', 'Rules'=>'all:9', 'Page'=>21, 'Key'=>false);
$tfield['vacina_nao_pq'] = array('DBName'=>'q2042','Type'=>0, 'CType'=>'check_box', 'Text'=>'Porque não tomou a vacina?', 'Rules'=>'all:9', 'Page'=>20, 'Key'=>false);

$tfield['sofre_doencas_check'] = array('DBName'=>'q2004','Type'=>0, 'CType'=>'check_box', 'Text'=>'Sofre de alguma das seguintes doenças?', 'Rules'=>'', 'Page'=>9, 'Key'=>false);
$tfield['e_fumador_radio'] = array('DBName'=>'q2005','Type'=>0, 'CType'=>'radio_btn', 'Text'=>'É fumador(a)?', 'Rules'=>'', 'Page'=>10, 'Key'=>false);
$tfield['fruta_legumes_radio'] = array('DBName'=>'q2006','Type'=>0, 'CType'=>'radio_btn', 'Text'=>'Costuma comer legumes e duas peças de fruta diariamente?', 'Rules'=>'', 'Page'=>11, 'Key'=>false);

$tfield['suplem_radio'] = array('DBName'=>'q2007','Type'=>0, 'CType'=>'radio_btn', 'Text'=>'Toma algum tipo de suplemento?', 'Rules'=>'all:22', 'Page'=>12, 'Key'=>false);
$tfield['statins'] = array('DBName'=>'q2055','Type'=>0, 'CType'=>'check_box', 'Text'=>'Toma algum medicamento com estatinas?', 'Rules'=>'all:13', 'Page'=>22, 'Key'=>false);

$tfield['desporto_radio'] = array('DBName'=>'q2008','Type'=>0, 'CType'=>'radio_btn', 'Text'=>'Com que frequência pratica desporto?', 'Rules'=>'', 'Page'=>13, 'Key'=>false);
$tfield['agregado_radio'] = array('DBName'=>'q2009','Type'=>0, 'CType'=>'radio_btn', 'Text'=>'Como caracteriza o seu agregado familiar?', 'Rules'=>'1,2:16;3:15', 'Page'=>14, 'Key'=>false);

$tfield['cria_freq_radio'] = array('DBName'=>'q2010','Type'=>0, 'CType'=>'radio_btn', 'Text'=>'As crianças frequentam creche ou escola?', 'Rules'=>'', 'Page'=>15, 'Key'=>false);
$tfield['animais_check'] = array('DBName'=>'q2011','Type'=>0, 'CType'=>'check_box', 'Text'=>'Tem animais de estimação?', 'Rules'=>'', 'Page'=>16, 'Key'=>false);

//DONT CHANGE THIS "newsletter_radio" (SEE FORM.CLASS)
$tfield['newsletter_radio'] = array('DBName'=>'q2012','Type'=>0, 'CType'=>'radio_btn', 'Text'=>'Deseja aderir à newsletter gripenet?', 'Rules'=>'all:23', 'Page'=>17, 'Key'=>false); //100, end it!
$tfield['contact_radio'] = array('DBName'=>'q2016','Type'=>0, 'CType'=>'radio_btn', 'Text'=>'Permissão para contacto extra', 'Rules'=>'all:100', 'Page'=>23, 'Key'=>false); //100, end it!

?>
