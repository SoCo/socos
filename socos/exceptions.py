""" socos.exceptions contains all exceptions raised within socos """


class SoCoIllegalSeekException(Exception):
    """ illegal seek exception which is raised when attempting to play a
    index outside of the queue """
    pass


class SocosException(Exception):
    """General socos exception"""
    pass
