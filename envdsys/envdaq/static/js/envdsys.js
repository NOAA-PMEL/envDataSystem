// Accordions
function doAccordion(id) {
    var menu = document.getElementById(id);
    var icon = document.getElementById(id+"-icon");
    // console.log(menu, icon, id)
    if (menu.className.indexOf("w3-show") == -1) {
        menu.className += " w3-show";
        icon.innerText = "expand_less"
    } else { 
        menu.className = menu.className.replace("w3-show", "");
        icon.innerText = "expand_more"
    }
}

function myAccordion(id) {
    var x = document.getElementById('accordion-'+id);
    var bi = document.getElementById('button-icon-'+id);
    // console.log(x, id)
    if (x.className.indexOf("w3-show") == -1) {
        x.className += " w3-show";
        bi.innerText = "expand_less"
    } else { 
        x.className = x.className.replace("w3-show", "");
        bi.innerText = "expand_more"
    }
}
