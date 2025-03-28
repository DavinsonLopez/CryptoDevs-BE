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
    ERROR_NOT_ADMIN = "El usuario no es administrador"

class VisitorMessages:
    # Success messages
    SUCCESS_VISITOR_CREATED = "Visitante registrado exitosamente"
    SUCCESS_VISITOR_UPDATED = "Visitante actualizado exitosamente"
    SUCCESS_VISITOR_DELETED = "Visitante eliminado exitosamente"

    # Error messages
    ERROR_VISITOR_NOT_FOUND = "Visitante no encontrado"
    ERROR_VISITOR_EMAIL_EXISTS = "Ya existe un visitante con este correo electrónico"
    ERROR_VISITOR_DOCUMENT_EXISTS = "Ya existe un visitante con este número de documento"

class AccessLogMessages:
    # Success messages
    SUCCESS_ACCESS_LOG_CREATED = "Registro de acceso creado exitosamente"
    SUCCESS_ACCESS_LOG_UPDATED = "Registro de acceso actualizado exitosamente"
    SUCCESS_ACCESS_LOG_DELETED = "Registro de acceso eliminado exitosamente"

    # Error messages
    ERROR_ACCESS_LOG_NOT_FOUND = "Registro de acceso no encontrado"
    ERROR_INVALID_PERSON_TYPE = "Tipo de persona inválido"
    ERROR_INVALID_ACCESS_TYPE = "Tipo de acceso inválido"
    ERROR_PERSON_NOT_FOUND = "Persona no encontrada"
    ERROR_USER_NOT_FOUND = "Usuario no encontrado"
    ERROR_VISITOR_NOT_FOUND = "Visitante no encontrado"

class IncidentMessages:
    # Success messages
    SUCCESS_INCIDENT_CREATED = "Incidente registrado exitosamente"
    SUCCESS_INCIDENT_UPDATED = "Incidente actualizado exitosamente"
    SUCCESS_INCIDENT_DELETED = "Incidente eliminado exitosamente"

    # Error messages
    ERROR_INCIDENT_NOT_FOUND = "Incidente no encontrado"

class SystemMessages:
    # Internal system messages (in English)
    HEALTH_CHECK_STATUS = "healthy"
    HEALTH_CHECK_MESSAGE = "Service is running"
    DB_CONNECTION_ERROR = "Database connection error"
    INTERNAL_SERVER_ERROR = "Internal server error"
