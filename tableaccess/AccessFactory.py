from tableaccess.TableHelper import TableHelper
from tableaccess.TableHelperSQLAlchemy import SQLAlchemyTableHelper
from tableaccess.CostByTimeSQLAlchemyHelper import CbyTSQLAlchemyTableHelper


class AccessFactory:
    @staticmethod
    def get_db_conn_service(use_alchemy=True):
        """
        TableHelper is based on sqlite which is not thread-safe
        i.e. you may get exceptions like https://stackoverflow.com/questions/48218065/programmingerror-sqlite-objects-created-in-a-thread-can-only-be-used-in-that-sa
        To avoid that use SQLAlchemy connection which works fine when shared b/w threads
        :param use_alchemy:
        :return:
        """
        if use_alchemy:
            return SQLAlchemyTableHelper()
        return TableHelper()

    @staticmethod
    def get_cost_by_time_db_conn():
        return CbyTSQLAlchemyTableHelper()
