<?php

// $basePath 	= dirname( __FILE__ );
// $basePath 	= dirname( __FILE__ );
// require( $basePath . '/form.class.php' );
// 
// global $my;
// define ( '_TABLE_NAME', 'table_profile_answers' ); 
// 
// $TOTAL_NUMBER_PAGES = 5;

//Página 1 
$tfield['sexo_radio'] = array('DBName'=>'sexo', 'Type'=>0, 'CType'=>'radio_btn', 'Text'=>'Sexo', 'Rules'=>'', 'Page'=>1, 'Key'=>false);

$tfield['mes_list'] = array('DBName'=>'mes', 'Type'=>0, 'CType'=>'select_list', 'Text'=>'Mes de Nascimento', 'Rules'=>'', 'Page'=>1, 'Key'=>false);

$tfield['ano_list'] = array('DBName'=>'ano', 'Type'=>0, 'CType'=>'select_list', 'Text'=>'Ano de Nascimento', 'Rules'=>'', 'Page'=>1, 'Key'=>false);

$tfield['cor_radio'] = array('DBName'=>'cor', 'Type'=>0, 'CType'=>'radio_btn', 'Text'=>'Cor', 'Rules'=>'', 'Page'=>1, 'Key'=>false);

//Página 2
$tfield['cidade_radio'] = array('DBName'=>'cidade', 'Type'=>0, 'CType'=>'radio_btn', 'Text'=>'Cidade', 'Rules'=>'', 'Page'=>2, 'Key'=>false);

$tfield['bairro_list'] = array('DBName'=>'bairro', 'Type'=>0, 'CType'=>'select_list', 'Text'=>'Bairro', 'Rules'=>'', 'Page'=>2, 'Key'=>false);

$tfield['rua_list'] = array('DBName'=>'rua', 'Type'=>0, 'CType'=>'select_list', 'Text'=>'Rua', 'Rules'=>'', 'Page'=>2, 'Key'=>false);

$tfield['numero_list'] = array('DBName'=>'numero', 'Type'=>0, 'CType'=>'select_list', 'Text'=>'Numero', 'Rules'=>'', 'Page'=>2, 'Key'=>false);

$tfield['zona_inf'] = array('DBName'=>'q1000', 'Type'=>0, 'CType'=>'hidden', 'Text'=>'zona_inf', 'Rules'=>'', 'Page'=>2, 'Key'=>false);

$tfield['setor'] = array('DBName'=>'setor', 'Type'=>0, 'CType'=>'hidden', 'Text'=>'setor', 'Rules'=>'', 'Page'=>2, 'Key'=>false);

$tfield['tipo_radio'] = array('DBName'=>'tipo', 'Type'=>0, 'CType'=>'radio_btn', 'Text'=>'Tipo de Residencia', 'Rules'=>'', 'Page'=>2, 'Key'=>false);

$tfield['andar_list'] = array('DBName'=>'andar', 'Type'=>0, 'CType'=>'select_list', 'Text'=>'Andar', 'Rules'=>'', 'Page'=>2, 'Key'=>false);

//Página 3
$tfield['escolaridade_radio'] = array('DBName'=>'escolaridade', 'Type'=>0, 'CType'=>'radio_btn', 'Text'=>'Escolaridade', 'Rules'=>'', 'Page'=>3, 'Key'=>false);

$tfield['atividade_radio'] = array('DBName'=>'atividade', 'Type'=>0, 'CType'=>'radio_btn', 'Text'=>'Atividade', 'Rules'=>'', 'Page'=>3, 'Key'=>false);

//Página 4
$tfield['diabetes_check'] = array('DBName'=>'diabetes', 'Type'=>0, 'CType'=>'check_box', 'Text'=>'Diabetes', 'Rules'=>'', 'Page'=>4, 'Key'=>false);

$tfield['autoimune_check'] = array('DBName'=>'auto_imune', 'Type'=>0, 'CType'=>'check_box', 'Text'=>'Auto Imune', 'Rules'=>'', 'Page'=>4, 'Key'=>false);

$tfield['pressao_check'] = array('DBName'=>'pressao_alta', 'Type'=>0, 'CType'=>'check_box', 'Text'=>'Pressão Alta', 'Rules'=>'', 'Page'=>4, 'Key'=>false);

$tfield['asma_check'] = array('DBName'=>'asma', 'Type'=>0, 'CType'=>'check_box', 'Text'=>'Asma', 'Rules'=>'', 'Page'=>4, 'Key'=>false);

$tfield['alergias_check'] = array('DBName'=>'alergias', 'Type'=>0, 'CType'=>'check_box', 'Text'=>'Alergias', 'Rules'=>'', 'Page'=>4, 'Key'=>false);

$tfield['diabetes_list'] = array('DBName'=>'m_diabetes', 'Type'=>0, 'CType'=>'select_list', 'Text'=>'Medicacao diabetes', 'Rules'=>'', 'Page'=>4, 'Key'=>false);

$tfield['autoimune_list'] = array('DBName'=>'m_auto_imune', 'Type'=>0, 'CType'=>'select_list', 'Text'=>'Medicacao auto imune', 'Rules'=>'', 'Page'=>4, 'Key'=>false);

$tfield['pressao_list'] = array('DBName'=>'m_pressao_alta', 'Type'=>0, 'CType'=>'select_list', 'Text'=>'Medicacao pressao alta', 'Rules'=>'', 'Page'=>4, 'Key'=>false);

$tfield['asma_list'] = array('DBName'=>'m_asma', 'Type'=>0, 'CType'=>'select_list', 'Text'=>'Medicacao asma', 'Rules'=>'', 'Page'=>4, 'Key'=>false);

$tfield['alergias_list'] = array('DBName'=>'m_alergias', 'Type'=>0, 'CType'=>'select_list', 'Text'=>'Medicacao alergias', 'Rules'=>'', 'Page'=>4, 'Key'=>false);

$tfield['dengue_radio'] = array('DBName'=>'dengue', 'Type'=>0, 'CType'=>'radio_btn', 'Text'=>'Teve dengue', 'Rules'=>'', 'Page'=>4, 'Key'=>false);

//Página 5
$tfield['valor_textarea'] = array('DBName'=>'valor', 'Type'=>0, 'CType'=>'text_area', 'Text'=>'Total de pessoas', 'Rules'=>'', 'Page'=>5, 'Key'=>false);

$tfield['newsletter_radio'] = array('DBName'=>'q2012','Type'=>0, 'CType'=>'radio_btn', 'Text'=>'Deseja se inscrever no newsletter do Dengue na Web', 'Rules'=>'', 'Page'=>5, 'Key'=>false);

//Inclusão dos dados
// $adesao = new Form("Questionário de Adesão", _TABLE_NAME, $TOTAL_NUMBER_PAGES);
// 
// foreach ( array_keys($tfield) as $key)
//   $adesao->add($key, $tfield[$key]['DBName'], $tfield[$key]['Type'], '', $tfield[$key]['Text'], $tfield[$key]['CType'], $tfield[$key]['Rules'], $tfield[$key]['Page'], $tfield[$key]['Key']);
// 
// $adesao->add("data", "date", 1, date("Y-m-d"), '', '', '', 0, false);
// $adesao->add("id", "uid", 2, $my->id, '', '', '', 0, true);

?>
