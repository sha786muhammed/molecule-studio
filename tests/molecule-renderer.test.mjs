import test from 'node:test';
import assert from 'node:assert/strict';
import {parseMolblock} from '../src/softwareViewer.js';
test('software viewer reads coordinates, elements and bond orders from MDL data',()=>{
 const block='Molecule\n  test\n\n  2  1  0  0  0  0            999 V2000\n    0.0000    1.0000   -2.0000 C   0  0  0  0  0  0  0  0  0  0  0  0\n    1.3000    1.0000   -2.0000 O   0  0  0  0  0  0  0  0  0  0  0  0\n  1  2  2  0\nM  END\n';
 const m=parseMolblock(block);assert.equal(m.atoms.length,2);assert.equal(m.atoms[0].z,-2);assert.equal(m.atoms[1].elem,'O');assert.deepEqual(m.bonds,[{a:0,b:1,order:2}]);
});
test('invalid molecular data is rejected instead of drawing invented atoms',()=>assert.throws(()=>parseMolblock('invalid')));
