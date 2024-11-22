<?php
session_start(); // Inicia a sessão

$host = "localhost";
$usuario = "root";
$senha = "";
$banco = "artmusic";
$conexao = new mysqli($host, $usuario, $senha, $banco);

if ($conexao->connect_error) {
    die("Conexão falhou: " . $conexao->connect_error);
}

$email = $_GET['email'];
$senha = $_GET['senha'];

$sql = $conexao->prepare("SELECT nome FROM usuarios WHERE email=? AND senha=?");
$sql->bind_param("ss", $email, $senha);
$sql->execute();
$result = $sql->get_result();

if ($result->num_rows > 0) {
    $row = $result->fetch_assoc();
    $_SESSION['usuario_nome'] = $row['nome']; 

    echo "<script>setTimeout(function() { window.location.href = 'index.php'; }, 1);</script>";

} else {
    echo "Credenciais inválidas.";
}

$conexao->close();
?>
