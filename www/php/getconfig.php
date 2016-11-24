<?php
// Parse without sections
$config = parse_ini_file("../config/config.ini");
echo json_encode($config);
?>