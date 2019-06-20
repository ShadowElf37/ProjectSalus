const screenWidth = document.documentElement.clientWidth;

function format(str) {
    if(arguments.length > 1) {
            const t = typeof arguments[1];
            const args = (t === 'string' || t === 'number')
                    ? Array.prototype.slice.call(arguments, 1)
                    : arguments[1];

            for(const key in args) {
                    str = str.replace(new RegExp('\\{' + key + '\\}', 'gi'), args[key]);
            }
    }
    return str;
}

function unique(array){
    return array.filter(function(value, index, self) { 
        return self.indexOf(value) === index;
    });
}

function clear(elem){
    while (elem.firstChild){
        elem.removeChild(elem.firstChild);
    };
}

function stripTimeZeroes(timeStr){
    if (timeStr.charAt(0) == 0){
        return timeStr.substring(1, timeStr.length);
    };  return timeStr;
}
function stripAmPm(timeStr){
    return timeStr.toLowerCase().replace('pm', '').replace('am', '').trim();
}
