// set up accordions
function setup_accordions() {
    var acc = document.getElementsByClassName("accordion");
    var i;

    for (i = 0; i < acc.length; i++) {
        acc[i].addEventListener("click", function () {
            this.classList.toggle("active");
            var panel = this.nextElementSibling;
            if (panel.style.maxHeight) {
                panel.style.maxHeight = null;
            } else {
                panel.style.maxHeight = panel.scrollHeight + "px";
            }
        });
    };
}

// function build_data_table() {

//     var tablediv = document.getElementById('meas-table')[0];
    
//     var table = document.createElement('table');
//     table.setAttribute('id', 'data-table');
//     table.setAttribute('style', 'border-collapse: collapse;')

//     var header = table.createTHead();
//     var row = header.insertRow(0);
//     row.setAttribute('style', 'border: 1px solid black')
//     var cell = row.insertCell(0);
//     cell.setAttribute('id', 'data-table-namecol');
//     cell.setAttribute('style', 'border: 1px solid black; text-align: center;')
//     cell.innerHTML = "<b>Name</b>";
//     cell = row.insertCell(1);
//     cell.setAttribute('style', 'border: 1px solid black; text-align: center;')
//     cell.innerHTML = "<b>Value</b>";
//     cell.setAttribute('id', 'data-table-valuecol');
//     cell = row.insertCell(2);
//     cell.setAttribute('style', 'border: 1px solid black; text-align: center;')
//     cell.innerHTML = "<b>Units</b>";
//     cell.setAttribute('id', 'data-table-unitcol');

//     if ('primary' in measurements['measurements']) {
//         primary = measurements['measurements']['primary']
//         for (var meas in primary) {
//             row = table.insertRow(1);
//             cell = row.insertCell(0);
//             cell.setAttribute('id', (meas+'-name'));
//             cell.setAttribute('style', 'border: 1px solid black; padding: 2px; text-align: center')
//             cell.innerHTML = meas
//             cell = row.insertCell(1);
//             cell.setAttribute('id', (meas+'-value'));
//             cell.setAttribute('style', 'border: 1px solid black; padding: 2px; text-align: center');
//             cell.innerHTML = '';                    
//             cell.setAttribute('id', (meas+'-units'));
//             cell.setAttribute('style', 'border: 1px solid black; padding: 2px; text-align: center');
//             cell.innerHTML = meas['units']                    
//         }
//     }
//     var td = table.rows[0].cells[0];
//     td.width = '200px';
//     td = table.rows[0].cells[1];
//     td.width = '200px';
//     td = table.rows[0].cells[1];
//     td.width = '100px';
   
//     tablediv.appendChild(table);
    

// }            
