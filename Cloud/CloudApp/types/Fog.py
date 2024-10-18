from ..dtos.FogSerializer import FogSerializer


class Fog:

    def __init__(self, dto: FogSerializer):
        self.address = dto['address']
        self.position_x = dto['positionX']
        self.position_y = dto['positionY']
        self.coverage_area = dto['coverageArea']

