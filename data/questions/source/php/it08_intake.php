<?php

$tfield = array();

$tfield['cod_postal_list'] = array('DBName'=>'q1000', 'Type'=>0, 'CType'=>'select_list','Text'=>'Codice postale dove vivi', 'Rules'=>'', 'Page'=>1, 'Key'=>false);
$tfield['cod_postal_list_work'] = array('DBName'=>'q1005', 'Type'=>0, 'CType'=>'select_list','Text'=>'Codice postale dove lavori/vai a scuola', 'Rules'=>'', 'Page'=>1, 'Key'=>false);  
$tfield['sexo_radio'] = array('DBName'=>'q1001', 'Type'=>0, 'CType'=>'radio_btn', 'Text'=>'Sesso', 'Rules'=>'', 'Page'=>1, 'Key'=>false);
$tfield['data_nasc_input'] = array('DBName'=>'q1002','Type'=>1, 'CType'=>'select_list', 'Text'=>'Data di Nascita', 'Rules'=>'', 'Page'=>1, 'Key'=>false); 

$tfield['ocupa_check'] = array('DBName'=>'q2000','Type'=>0, 'CType'=>'check_box', 'Text'=>'Occupazione giornaliera', 'Rules'=>'', 'Page'=>2, 'Key'=>false); 

$tfield['meio_transp_check'] = array('DBName'=>'q2001','Type'=>0, 'CType'=>'check_box', 'Text'=>'Quale il mezzo di trasporto che usi quotidianamente?', 'Rules'=>'', 'Page'=>3, 'Key'=>false);

$tfield['const_ano_radio'] = array('DBName'=>'q2002','Type'=>0, 'CType'=>'radio_btn', 'Text'=>'In media, quante volte ti ammali in un anno?', 'Rules'=>'', 'Page'=>4, 'Key'=>false);

$tfield['vacina_grip_radio'] = array('DBName'=>'q2040','Type'=>0, 'CType'=>'radio_btn', 'Text'=>'Ti sei vaccinato contro l\'influenza, quest\'anno?', 'Rules'=>'1:13;2:12', 'Page'=>5, 'Key'=>false);

$tfield['vacina_siflu_noh1n1_pq'] = array('DBName'=>'q2041','Type'=>0, 'CType'=>'check_box', 'Text'=>'Perché hai deciso di vaccinarti?', 'Rules'=>'all:6', 'Page'=>13, 'Key'=>false);

$tfield['vacina_noflu_noh1n1_pq'] = array('DBName'=>'q2042','Type'=>0, 'CType'=>'check_box', 'Text'=>'Perché hai deciso di non vaccinarti?', 'Rules'=>'all:6', 'Page'=>12, 'Key'=>false);


// $tfield['vacina_sim_pq'] = array('DBName'=>'q2041','Type'=>0, 'CType'=>'check_box', 'Text'=>'Perché hai deciso di vaccinarti?', 'Rules'=>'all:6', 'Page'=>13, 'Key'=>false);
// 
// $tfield['vacina_nao_pq'] = array('DBName'=>'q2042','Type'=>0, 'CType'=>'check_box', 'Text'=>'Perché hai deciso di non vaccinarti?', 'Rules'=>'all:6', 'Page'=>12, 'Key'=>false);
// 



$tfield['sofre_doencas_check'] = array('DBName'=>'q2004','Type'=>0, 'CType'=>'check_box', 'Text'=>'Soffri di una delle seguenti patologie?', 'Rules'=>'', 'Page'=>6, 'Key'=>false);

$tfield['e_fumador_radio'] = array('DBName'=>'q2005','Type'=>0, 'CType'=>'radio_btn', 'Text'=>'Sei un fumatore/fumatrice?', 'Rules'=>'', 'Page'=>7, 'Key'=>false);

//$tfield['fruta_legumes_radio'] = array('DBName'=>'q2006','Type'=>0, 'CType'=>'radio_btn', 'Text'=>'Mangi abitualmente verdure e due porzioni di frutta quotidianamente?', 'Rules'=>'', 'Page'=>11, 'Key'=>false);
//$tfield['suplem_radio'] = array('DBName'=>'q2007','Type'=>0, 'CType'=>'radio_btn', 'Text'=>'Assumi qualche tipo di integratore vitaminico?', 'Rules'=>'all:22', 'Page'=>12, 'Key'=>false);
//$tfield['statins'] = array('DBName'=>'q2055','Type'=>0, 'CType'=>'check_box', 'Text'=>'Hai assunto farmaci della classe delle statine?
//', 'Rules'=>'all:13', 'Page'=>22, 'Key'=>false);

$tfield['desporto_radio'] = array('DBName'=>'q2008','Type'=>0, 'CType'=>'radio_btn', 'Text'=>'Con che frequenza pratichi attivita\' sportiva?', 'Rules'=>'', 'Page'=>8, 'Key'=>false);

$tfield['agregado_radio'] = array('DBName'=>'q2009','Type'=>0, 'CType'=>'radio_btn', 'Text'=>'Come si caratterizza il tuo nucleo familiare?', 'Rules'=>'1,2:11;3:10', 'Page'=>9, 'Key'=>false);

$tfield['cria_freq_radio'] = array('DBName'=>'q2010','Type'=>0, 'CType'=>'radio_btn', 'Text'=>'I bambini frequentano l\'asilo o la scuola?', 'Rules'=>'', 'Page'=>10, 'Key'=>false);

$tfield['animais_check'] = array('DBName'=>'q2011','Type'=>0, 'CType'=>'check_box', 'Text'=>'Hai animali da compagnia?', 'Rules'=>'all:14', 'Page'=>11, 'Key'=>false);

$tfield['info_check'] = array('DBName'=>'q2060','Type'=>0, 'CType'=>'check_box', 'Text'=>'Come sei venuto a conoscenza di Influweb?', 'Rules'=>'all:100', 'Page'=>14, 'Key'=>false);


//DONT CHANGE THIS "newsletter_radio" (SEE FORM.CLASS)
//$tfield['newsletter_radio'] = array('DBName'=>'q2012','Type'=>0, 'CType'=>'radio
//_btn', 'Text'=>'Desideri iscriverti alla newsletter di influweb?', 'Rules'=>'all
//:100', 'Page'=>12, 'Key'=>false); //100, end it!

//$tfield['contact_radio'] = array('DBName'=>'q2016','Type'=>0, 'CType'=>'radio_bt
//n', 'Text'=>'Autorizzi che lo staff', 'Rules'=>'all:100', 'Page'=>13, 'Key'=>false); //100, end it!

?>
