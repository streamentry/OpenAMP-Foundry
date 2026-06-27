from openamp_foundry.features.physchem import compute_features, net_charge_proxy


def test_net_charge_proxy():
    assert net_charge_proxy("KKD") == 1
    assert net_charge_proxy("DEK") == -1


def test_compute_features_length():
    features = compute_features("KWKLFKKIGAVLKVL")
    assert features["length"] == 15
    assert features["net_charge_proxy"] > 0
