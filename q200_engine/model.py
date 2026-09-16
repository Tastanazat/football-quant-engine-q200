from dataclasses import dataclass, asdict
from typing import Dict, Any


@dataclass(frozen=True)
class ModelSnapshot:
    """
    Q200 modelinin kilitlenebilir snapshot'ı.

    Odds aşamasından önce oluşturulur.
    Model LOCK edildikten sonra odds verisi model parametrelerini
    değiştiremez.
    """

    lambda_home: float
    lambda_away: float
    probabilities: Dict[str, float]
    locked: bool = False
    model_version: str = "Q200-V1"


class Q200Model:
    """
    Q200 model çekirdeği.

    Sorumlulukları:
    - λ Home / λ Away üretmek
    - Model olasılıklarını saklamak
    - Model snapshot oluşturmak
    - Modeli LOCK etmek
    - LOCK sonrası modelin değiştirilmesini engellemek
    """

    def __init__(
        self,
        lambda_home: float,
        lambda_away: float,
        probabilities: Dict[str, float],
        model_version: str = "Q200-V1",
    ):
        self._validate_lambda(lambda_home, "lambda_home")
        self._validate_lambda(lambda_away, "lambda_away")
        self._validate_probabilities(probabilities)

        self._lambda_home = float(lambda_home)
        self._lambda_away = float(lambda_away)
        self._probabilities = dict(probabilities)
        self._model_version = model_version
        self._locked = False

    @staticmethod
    def _validate_lambda(value: float, name: str) -> None:
        if value < 0:
            raise ValueError(f"{name} cannot be negative")

    @staticmethod
    def _validate_probabilities(
        probabilities: Dict[str, float]
    ) -> None:

        required = {"HOME", "DRAW", "AWAY"}

        if not isinstance(probabilities, dict):
            raise TypeError("probabilities must be a dictionary")

        missing = required - set(probabilities.keys())

        if missing:
            raise ValueError(
                f"Missing probabilities: {sorted(missing)}"
            )

        for outcome in required:
            probability = float(probabilities[outcome])

            if probability < 0 or probability > 1:
                raise ValueError(
                    f"Invalid probability for {outcome}: "
                    f"{probability}"
                )

        total = sum(
            float(probabilities[outcome])
            for outcome in required
        )

        # Küçük floating-point farklarına izin ver.
        if abs(total - 1.0) > 1e-6:
            raise ValueError(
                f"Probabilities must sum to 1.0, got {total}"
            )

    @property
    def lambda_home(self) -> float:
        return self._lambda_home

    @property
    def lambda_away(self) -> float:
        return self._lambda_away

    @property
    def probabilities(self) -> Dict[str, float]:
        return dict(self._probabilities)

    @property
    def locked(self) -> bool:
        return self._locked

    @property
    def model_version(self) -> str:
        return self._model_version

    def snapshot(self) -> ModelSnapshot:
        """
        Modelin mevcut durumunu immutable snapshot olarak döndürür.
        """

        return ModelSnapshot(
            lambda_home=self._lambda_home,
            lambda_away=self._lambda_away,
            probabilities=dict(self._probabilities),
            locked=self._locked,
            model_version=self._model_version,
        )

    def lock(self) -> ModelSnapshot:
        """
        Modeli LOCK eder.

        LOCK sonrası λ ve olasılıklar değiştirilemez.
        """

        self._locked = True

        return self.snapshot()

    def update(
        self,
        lambda_home: float,
        lambda_away: float,
        probabilities: Dict[str, float],
    ) -> None:
        """
        Modeli günceller.

        Model LOCK edilmişse güncelleme yasaktır.
        """

        if self._locked:
            raise RuntimeError(
                "Model is locked and cannot be modified"
            )

        self._validate_lambda(lambda_home, "lambda_home")
        self._validate_lambda(lambda_away, "lambda_away")
        self._validate_probabilities(probabilities)

        self._lambda_home = float(lambda_home)
        self._lambda_away = float(lambda_away)
        self._probabilities = dict(probabilities)

    def to_dict(self) -> Dict[str, Any]:
        """
        Model durumunu JSON/raporlama için dictionary olarak döndürür.
        """

        return {
            "lambda_home": self._lambda_home,
            "lambda_away": self._lambda_away,
            "probabilities": dict(self._probabilities),
            "locked": self._locked,
            "model_version": self._model_version,
        }


def create_model(
    lambda_home: float,
    lambda_away: float,
    probabilities: Dict[str, float],
    model_version: str = "Q200-V1",
) -> Q200Model:
    """
    Q200 model factory.
    """

    return Q200Model(
        lambda_home=lambda_home,
        lambda_away=lambda_away,
        probabilities=probabilities,
        model_version=model_version,
    )


def lock_model(model: Q200Model) -> ModelSnapshot:
    """
    Modeli dışarıdan LOCK etmek için yardımcı fonksiyon.
    """

    return model.lock()


def model_to_dict(model: Q200Model) -> Dict[str, Any]:
    """
    Modeli dictionary formatına çevirir.
    """

    return model.to_dict()
