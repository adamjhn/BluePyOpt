"""Test ephys model objects"""

import os
import tempfile
import contextlib


import pytest
import numpy

from bluepyopt import ephys

sim = ephys.simulators.NrnSimulator()
TESTDATA_DIR = os.path.join(
    os.path.dirname(
        os.path.abspath(__file__)),
    'testdata')
simple_morphology_path = os.path.join(TESTDATA_DIR, 'simple.swc')
apic_morphology_path = os.path.join(TESTDATA_DIR, 'apic.swc')


@contextlib.contextmanager
def yield_blank_hoc(template_name):
    """Create blank hoc template"""
    hoc_template = ephys.models.CellModel.create_empty_template(template_name)
    temp_file = tempfile.NamedTemporaryFile(suffix='test_models')
    with temp_file as fd:
        fd.write(hoc_template.encode('utf-8'))
        fd.flush()
        yield temp_file.name


test_morph = ephys.morphologies.NrnFileMorphology(simple_morphology_path)


@pytest.mark.unit
def test_create_empty_template():
    """ephys.models: Test creation of empty template"""
    template_name = 'FakeTemplate'
    hoc_template = ephys.models.CellModel.create_empty_template(template_name)
    sim.neuron.h(hoc_template)
    assert hasattr(sim.neuron.h, template_name)


@pytest.mark.unit
def test_model():
    """ephys.models: Test Model class"""
    model = ephys.models.Model('test_model')
    model.instantiate(sim=None)
    model.destroy(sim=None)
    assert isinstance(model, ephys.models.Model)


@pytest.mark.unit
def test_cellmodel():
    """ephys.models: Test CellModel class"""
    model = ephys.models.CellModel('test_model', morph=test_morph, mechs=[])

    assert (
        str(model)
        == 'test_model:\n  morphology:\n    %s\n  mechanisms:\n  params:\n' %
        simple_morphology_path)

    model.instantiate(sim=sim)
    model.destroy(sim=sim)
    assert isinstance(model, ephys.models.CellModel)


@pytest.mark.unit
def test_cellmodel_namecheck():
    """ephys.models: Test CellModel class name checking"""

    # Test valid name
    for name in ['test3', 'test_3']:
        ephys.models.CellModel(name, morph=test_morph, mechs=[])

    # Test invalid names
    for name in ['3test', '', 'test$', 'test 3']:
        pytest.raises(
            TypeError,
            ephys.models.CellModel,
            name,
            morph=test_morph,
            mechs=[])


@pytest.mark.unit
def test_load_hoc_template():
    """ephys.models: Test loading of hoc template"""

    template_name = 'test_load_hoc'
    hoc_string = ephys.models.CellModel.create_empty_template(template_name)
    ephys.models.HocCellModel.load_hoc_template(sim, hoc_string)
    assert hasattr(sim.neuron.h, template_name)


@pytest.mark.unit
def test_HocCellModel():
    """ephys.models: Test HOCCellModel class"""
    template_name = 'test_HocCellModel'
    hoc_string = ephys.models.CellModel.create_empty_template(template_name)
    hoc_cell = ephys.models.HocCellModel(
        'test_hoc_model', simple_morphology_path, hoc_string=hoc_string)
    hoc_cell.instantiate(sim)
    assert hoc_cell.icell is not None
    assert hoc_cell.cell is not None

    assert 'simple.swc' in str(hoc_cell)

    # these should be callable, but don't do anything
    hoc_cell.freeze(None)
    hoc_cell.unfreeze(None)
    hoc_cell.check_nonfrozen_params(None)
    hoc_cell.params_by_names(None)

    hoc_cell.destroy(sim=sim)


@pytest.mark.unit
def test_CellModel_create_empty_cell():
    """ephys.models: Test create_empty_cell"""
    template_name = 'create_empty_cell'
    cell = ephys.models.CellModel.create_empty_cell(template_name, sim)
    assert callable(cell)
    assert hasattr(sim.neuron.h, template_name)


@pytest.mark.unit
def test_CellModel_create_hoc():
    """ephys.models: Test create_hoc"""

    morph0 = ephys.morphologies.NrnFileMorphology(
        simple_morphology_path,
        do_replace_axon=True)

    cell_model = ephys.models.CellModel('CellModel',
                                        morph=morph0,
                                        mechs=[],
                                        params=[])

    hoc_string = cell_model.create_hoc({})
    assert 'begintemplate CellModel' in hoc_string
    assert 'proc replace_axon()' in hoc_string
    cell_model_hoc = ephys.models.HocCellModel(
        'CellModelHOC',
        simple_morphology_path,
        hoc_string=hoc_string)

    assert isinstance(cell_model_hoc, ephys.models.HocCellModel)


@pytest.mark.unit
def test_CellModel_destroy():
    """ephys.models: Test CellModel destroy"""
    morph0 = ephys.morphologies.NrnFileMorphology(simple_morphology_path)
    cell_model0 = ephys.models.CellModel('CellModel_destroy',
                                         morph=morph0,
                                         mechs=[],
                                         params=[])
    morph1 = ephys.morphologies.NrnFileMorphology(simple_morphology_path)
    cell_model1 = ephys.models.CellModel('CellModel_destroy',
                                         morph=morph1,
                                         mechs=[],
                                         params=[])

    assert not hasattr(sim.neuron.h, 'CellModel_destroy')

    cell_model0.instantiate(sim=sim)
    assert hasattr(sim.neuron.h, 'CellModel_destroy')
    assert 1 == len(sim.neuron.h.CellModel_destroy)

    cell_model1.instantiate(sim=sim)
    assert 2 == len(sim.neuron.h.CellModel_destroy)

    # make sure cleanup works
    cell_model0.destroy(sim=sim)
    assert 1 == len(sim.neuron.h.CellModel_destroy)

    cell_model1.destroy(sim=sim)
    assert 0 == len(sim.neuron.h.CellModel_destroy)


@pytest.mark.unit
def test_lfpy_create_empty_template():
    """ephys.models: Test creation of lfpy empty template"""
    template_name = 'FakeTemplate'
    hoc_template = ephys.models.LFPyCellModel.create_empty_template(
        template_name
    )
    sim.neuron.h(hoc_template)
    assert hasattr(sim.neuron.h, template_name)


@pytest.mark.unit
def test_lfpycellmodel():
    """ephys.models: Test LFPyCellModel class"""
    model = ephys.models.LFPyCellModel('test_lfpy_model', morph=test_morph,
                                       mechs=[], v_init=-80)

    assert (
        str(model)
        == 'test_lfpy_model:\n  morphology:\n    %s\n  '
           'mechanisms:\n  params:\n' %
        simple_morphology_path)

    model.instantiate(sim=sim)
    model.destroy(sim=sim)
    assert isinstance(model, ephys.models.LFPyCellModel)


@pytest.mark.unit
def test_lfpycellmodel_namecheck():
    """ephys.models: Test LFPyCellModel class name checking"""

    # Test valid name
    for name in ['test3', 'test_3']:
        ephys.models.LFPyCellModel(name, morph=test_morph, mechs=[])

    # Test invalid names
    for name in ['3test', '', 'test$', 'test 3']:
        with pytest.raises(TypeError):
            ephys.models.LFPyCellModel(name, morph=test_morph, mechs=[])


@pytest.mark.unit
def test_load_lfpy_hoc_template():
    """ephys.models: Test loading of hoc template with lfpy cell"""

    template_name = 'test_load_hoc'
    hoc_string = ephys.models.LFPyCellModel.create_empty_template(
        template_name
    )
    ephys.models.HocCellModel.load_hoc_template(sim, hoc_string)
    assert hasattr(sim.neuron.h, template_name)


@pytest.mark.unit
def test_LFPyCellModel_create_empty_cell():
    """ephys.models: Test create_empty_cell with lfpy cell"""
    template_name = 'create_empty_cell'
    cell = ephys.models.LFPyCellModel.create_empty_cell(template_name, sim)
    assert callable(cell)
    assert hasattr(sim.neuron.h, template_name)


@pytest.mark.unit
def test_LFPyCellModel_create_hoc():
    """ephys.models: Test create_hoc with lfpy cell"""

    morph0 = ephys.morphologies.NrnFileMorphology(
        simple_morphology_path,
        do_replace_axon=True
    )

    cell_model = ephys.models.LFPyCellModel(
        'LFPyCellModel',
        morph=morph0,
        mechs=[],
        params=[]
    )

    hoc_string = cell_model.create_hoc({})
    assert 'begintemplate LFPyCellModel' in hoc_string
    assert 'proc replace_axon()' in hoc_string
    cell_model_hoc = ephys.models.HocCellModel(
        'CellModelHOC',
        simple_morphology_path,
        hoc_string=hoc_string)

    assert isinstance(cell_model_hoc, ephys.models.HocCellModel)


@pytest.mark.unit
def test_LFPyCellModel_destroy():
    """ephys.models: Test LFPyCellModel destroy"""
    morph0 = ephys.morphologies.NrnFileMorphology(simple_morphology_path)
    cell_model0 = ephys.models.LFPyCellModel(
        'LFPyCellModel_destroy', morph=morph0, mechs=[], params=[]
    )
    morph1 = ephys.morphologies.NrnFileMorphology(simple_morphology_path)
    cell_model1 = ephys.models.LFPyCellModel(
        'LFPyCellModel_destroy', morph=morph1, mechs=[], params=[]
    )

    assert not hasattr(sim.neuron.h, 'LFPyCellModel_destroy')

    cell_model0.instantiate(sim=sim)
    assert hasattr(sim.neuron.h, 'LFPyCellModel_destroy')
    assert 1 == len(sim.neuron.h.LFPyCellModel_destroy)

    cell_model1.instantiate(sim=sim)
    assert 2 == len(sim.neuron.h.LFPyCellModel_destroy)

    # make sure cleanup works
    cell_model0.destroy(sim=sim)
    assert 1 == len(sim.neuron.h.LFPyCellModel_destroy)

    cell_model1.destroy(sim=sim)
    assert 0 == len(sim.neuron.h.LFPyCellModel_destroy)


@pytest.mark.unit
def test_metaparameter():
    """ephys.models: Test model with MetaParameter"""

    morph = ephys.morphologies.NrnFileMorphology(apic_morphology_path)

    dist = "({A} + {B} * math.exp({distance} * {C})) * {value}"

    scaler = ephys.parameterscalers.NrnSegmentSomaDistanceScaler(
        distribution=dist, dist_param_names=['A', 'B', 'C'])

    all_loc = ephys.locations.NrnSeclistLocation('all', 'all')

    paramA = ephys.parameters.MetaParameter('ParamA', scaler, 'A', -1)
    paramB = ephys.parameters.MetaParameter(
        'ParamB',
        scaler,
        'B',
        bounds=[1.0, 3.0])
    paramC = ephys.parameters.MetaParameter(
        'ParamC',
        obj=scaler,
        attr_name='C',
        value=0.003,
        frozen=True)

    cm = ephys.parameters.NrnRangeParameter(
        name='cm',
        param_name='cm',
        bounds=[.5, 1.5],
        value_scaler=scaler,
        locations=[all_loc])

    test_params = {'ParamA': -1, 'ParamB': 2.0, 'cm': 1.0}

    cell_model = ephys.models.CellModel('CellModel',
                                        morph=morph,
                                        mechs=[],
                                        params=[cm, paramA, paramB, paramC])

    pytest.raises(Exception,
                  cell_model.freeze,
                  {'ParamC': 2.0})

    cell_model.freeze(test_params)

    cell_model.instantiate(sim=sim)

    assert (scaler.eval_dist(1.0, 1.0)
            == '(-1 + 2.0 * math.exp(1 * 0.003)) * 1')

    numpy.testing.assert_almost_equal(
        scaler.scale(
            1.0,
            cell_model.icell.apic[0](.5),
            sim=sim),
        1.0764239941636502)

    cell_model.unfreeze(param_names=['ParamA', 'ParamB'])

    hoc_code = cell_model.create_hoc(param_values=test_params)

    assert ('distribute_distance(CellRef.all, "cm", "(-1 + 2.0 * '
            'exp(%.17g * 0.003)) * 1")' in hoc_code)

    cell_model.destroy(sim=sim)

    hoc_model = ephys.models.HocCellModel(
        'hoc_model', '.', hoc_string=hoc_code)
    hoc_model.instantiate(sim=sim)
    hoc_model.destroy()
