from supabase import create_client
import time

url = "https://zhuyytyhkmahjohqbsqd.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpodXl5dHloa21haGpvaHFic3FkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzI4Nzg4NTMsImV4cCI6MjA0ODQ1NDg1M30.cyD6WqNNuGI4kPhtYSjBJ5TNennRxCnizcTrbRH-ufM"

supabase = create_client(url, key)


# Aguardar 6 segundos entre tentativas
time.sleep(6)

# Criar conta
response = supabase.auth.sign_up({
    'email': 'newuser@example.com',
    'password': 'password123'
})

if response.user is None:
    print(f"Erro: {response.error['message']}")
else:
    print("Usuário registrado com sucesso!")

