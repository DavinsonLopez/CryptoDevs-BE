class UserMessages:
    # Success messages
    SUCCESS_USER_CREATED = "Usuario creado exitosamente"
    SUCCESS_USER_UPDATED = "Usuario actualizado exitosamente"
    SUCCESS_USER_DELETED = "Usuario eliminado exitosamente"

    # Error messages
    ERROR_ADMIN_PASSWORD_REQUIRED = "La contraseña es obligatoria para usuarios administradores"
    ERROR_EMAIL_EXISTS = "Ya existe un usuario con este correo electrónico"
    ERROR_DOCUMENT_EXISTS = "Ya existe un usuario con este número de documento"
    ERROR_INVALID_CREDENTIALS = "Credenciales inválidas"
    ERROR_USER_NOT_FOUND = "Usuario no encontrado"
    ERROR_DATABASE_VALIDATION = "Error de validación en la base de datos"

class SystemMessages:
    # Internal system messages (in English)
    HEALTH_CHECK_STATUS = "healthy"
    HEALTH_CHECK_MESSAGE = "Service is running"
    DB_CONNECTION_ERROR = "Database connection error"
    INTERNAL_SERVER_ERROR = "Internal server error"
