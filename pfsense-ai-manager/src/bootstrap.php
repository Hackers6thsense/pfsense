<?php
/**
 * Application Bootstrap
 */

error_reporting(E_ALL);
ini_set('display_errors', 0);

// Define base path
define('BASE_PATH', dirname(__DIR__));
define('SRC_PATH', BASE_PATH . '/src');

// Autoloading
require_once BASE_PATH . '/vendor/autoload.php';

// Load environment variables
$dotenv = new \Dotenv\Dotenv(BASE_PATH);
if (file_exists(BASE_PATH . '/.env')) {
    $dotenv->load();
} elseif (file_exists(BASE_PATH . '/.env.example')) {
    throw new Exception('Please copy .env.example to .env and configure your settings');
}

// Initialize logger
use PfSenseAI\Utils\Logger;
$logger = Logger::getInstance();

// Set error handlers
set_error_handler(function($errno, $errstr, $errfile, $errline) use ($logger) {
    $logger->error("PHP Error: $errstr in $errfile:$errline");
    return false;
});

set_exception_handler(function($exception) use ($logger) {
    $logger->error($exception->getMessage());
});

// Load configuration
$config = new \PfSenseAI\Utils\Config();

// Enable CORS if needed
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, Authorization');
header('Content-Type: application/json');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

define('BOOTSTRAP_LOADED', true);
