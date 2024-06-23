from passlib.context import CryptContext

# Configuración de PassLib para usar argon2
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# Contraseña a aplicar hash
print("Contraseña")
password = input()

# Generar el hash de la contraseña
hashed_password = pwd_context.hash(password)

print(hashed_password)
