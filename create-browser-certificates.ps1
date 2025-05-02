# Create Browser-Friendly SSL Certificates
# This script creates a root CA and server certificate that browsers are more likely to trust
# Run as Administrator for best results

# Function to check if directory exists, if not create it
function Ensure-Directory {
    param([string]$DirectoryPath)
    
    if (-not (Test-Path -Path $DirectoryPath)) {
        New-Item -Path $DirectoryPath -ItemType Directory | Out-Null
        Write-Host "Created directory: $DirectoryPath" -ForegroundColor Green
    }
}

# Create necessary directories
$scriptDir = $PSScriptRoot
$sslDir = "$scriptDir\.cert"
Ensure-Directory -DirectoryPath $sslDir
Set-Location $sslDir

Write-Host "Generating new SSL certificates..." -ForegroundColor Cyan

# Get the host name for the certificate - default to csavn.ddns.net if empty
$hostname = Read-Host "Enter your domain name (default: csavn.ddns.net)"
if ([string]::IsNullOrWhiteSpace($hostname)) {
    $hostname = "csavn.ddns.net"
}

# Create configuration file for Root CA
$rootCAConfig = @"
[req]
distinguished_name = req_distinguished_name
prompt = no
x509_extensions = v3_ca

[req_distinguished_name]
CN = CSA Hello Root CA

[v3_ca]
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid:always,issuer:always
basicConstraints = critical, CA:true
keyUsage = critical, digitalSignature, cRLSign, keyCertSign
"@

# Create configuration file for Server Certificate
$serverConfig = @"
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
CN = $hostname

[v3_req]
basicConstraints = CA:FALSE
keyUsage = digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = $hostname
DNS.2 = localhost
IP.1 = 127.0.0.1
"@

# Write configurations to files
$rootCAConfig | Out-File -FilePath "rootCA.cnf" -Encoding ascii
$serverConfig | Out-File -FilePath "server.cnf" -Encoding ascii

Write-Host "Generating Root CA private key and certificate..." -ForegroundColor Cyan

# Generate Root CA private key and certificate
openssl genrsa -out rootCA.key 4096
if ($LASTEXITCODE -ne 0) { 
    Write-Error "Failed to generate Root CA key"
    exit 1
}

openssl req -x509 -new -nodes -key rootCA.key -sha256 -days 3650 -out rootCA.crt -config rootCA.cnf
if ($LASTEXITCODE -ne 0) { 
    Write-Error "Failed to generate Root CA certificate"
    exit 1
}

Write-Host "Generating Server private key and certificate signing request..." -ForegroundColor Cyan

# Generate Server private key and CSR
openssl genrsa -out server.key 2048
if ($LASTEXITCODE -ne 0) { 
    Write-Error "Failed to generate server key"
    exit 1
}

openssl req -new -key server.key -out server.csr -config server.cnf
if ($LASTEXITCODE -ne 0) { 
    Write-Error "Failed to generate certificate request"
    exit 1
}

Write-Host "Signing server certificate with Root CA..." -ForegroundColor Cyan

# Sign the server certificate with the Root CA
openssl x509 -req -in server.csr -CA rootCA.crt -CAkey rootCA.key -CAcreateserial -out server.crt -days 825 -extensions v3_req -extfile server.cnf
if ($LASTEXITCODE -ne 0) { 
    Write-Error "Failed to sign server certificate"
    exit 1
}

# Create a full certificate chain file
Get-Content server.crt, rootCA.crt | Out-File -FilePath "fullchain.crt" -Encoding ascii
Get-Content server.key | Out-File -FilePath "private.key" -Encoding ascii

# Convert to PEM format
Copy-Item "fullchain.crt" -Destination "cert.pem"
Copy-Item "private.key" -Destination "key.pem"

Write-Host "Certificates generated successfully!" -ForegroundColor Green
Write-Host "------------------------------------------" -ForegroundColor Green
Write-Host "Root CA Certificate: rootCA.crt" -ForegroundColor Green
Write-Host "Server Certificate: server.crt" -ForegroundColor Green
Write-Host "Private Key: server.key" -ForegroundColor Green
Write-Host "Full Chain: fullchain.crt" -ForegroundColor Green
Write-Host "PEM Files: cert.pem, key.pem" -ForegroundColor Green

Write-Host "`nInstalling Root CA into Windows Certificate Store..." -ForegroundColor Cyan

# Import Root CA into the Windows Certificate Store
$rootCertPath = Join-Path -Path $sslDir -ChildPath "rootCA.crt"
Write-Host "Looking for Root CA certificate at: $rootCertPath" -ForegroundColor Yellow

if (Test-Path $rootCertPath) {
    try {
        $rootCert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($rootCertPath)
        $store = New-Object System.Security.Cryptography.X509Certificates.X509Store("Root", "LocalMachine")
        $store.Open("ReadWrite")
        $store.Add($rootCert)
        $store.Close()
        Write-Host "Root CA installed in Windows Certificate Store!" -ForegroundColor Green
    }
    catch {
        Write-Host "Failed to install certificate: $_" -ForegroundColor Red
        Write-Host "You may need to run this script as Administrator" -ForegroundColor Red
    }
}
else {
    Write-Host "Root CA certificate file not found at $rootCertPath" -ForegroundColor Red
    Write-Host "Certificate was generated but could not be installed automatically" -ForegroundColor Red
}

Write-Host "Please restart your application for changes to take effect." -ForegroundColor Yellow
Write-Host "`nTo distribute the certificate to other computers, use the certificate installer page:" -ForegroundColor Magenta
Write-Host "https://$($hostname):8000/install-certificate" -ForegroundColor Magenta

# Go back to the original directory
Set-Location ..
