from tests.e2e.utils.infrastructure import BaseInfrastructure


class ParserStack(BaseInfrastructure):
    def create_resources(self):
        self.create_lambda_functions()
