import data from '../../data/data.json'

const champ = 'Ezreal';
const patches = data[champ].patch;
const prob = data[champ].prob;

let patch_map = {};
for (const patch of patches) {
    const [major, minor] = patch.split('.');
    if (!(major in patch_map)) {
        patch_map[major] = [];
    }
    patch_map[major].push(minor);
}
patch_map = Object.entries(patch_map);
patch_map.sort((a, b) => parseInt(a) - parseInt(b));

console.log(patch_map);

const table = document.createElement('table');
{
    const row = table.insertRow();
    for (const [idx, dt] of patch_map.entries()) {
        const major = dt[0];
        const cell = row.insertCell();
        cell.textContent = major;
    }
}

let maxSubPatchCnt = 0;
for (const [_, sub] of patch_map) {
    maxSubPatchCnt = Math.max(maxSubPatchCnt, sub.length);
}

for (let i = 0; i < maxSubPatchCnt; ++i) {
    const row = table.insertRow();
    for (const [_, sub] of patch_map) {
        if (i > sub.length) {
            continue;
        }
        if (i == sub.length) {
            const cell = row.insertCell();
            cell.rowSpan = maxSubPatchCnt - sub.length;
            continue;
        }

        const cell = row.insertCell();
        cell.textContent = sub[i];
    }
}

document.getElementById('app').appendChild(table);
