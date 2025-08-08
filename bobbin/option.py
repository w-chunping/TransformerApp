class WireOption:
    def __init__(self,
                 ji_list: list[float] = None, 
                 pi_list: list[int] = None, 
                 spi_list: list[int] = None,
                 insulator_thickness: float = 0.03e-3,
                 kwb: float = 0.9,
                 khb: float = 0.8,
                 ht: float = 0.05e-3,
                 lt: float = None,
                 kf: float = 0.2    # for kf method
                 ):
        self.ji_list = ji_list
        self.pi_list = pi_list
        self.spi_list = spi_list
        self.insulator_thickness = insulator_thickness
        self.kwb = kwb
        self.khb = khb
        self.ht = ht
        self.lt = lt
        self.kf = kf
        