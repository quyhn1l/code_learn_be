class UserRole:
    ADMIN = "admin"
    INSTRUCTOR = "instructor"
    STUDENT = "student"
    
    @classmethod
    def get_valid_roles(cls):
        return [cls.ADMIN, cls.INSTRUCTOR, cls.STUDENT]