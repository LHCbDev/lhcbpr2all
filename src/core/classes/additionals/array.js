/**
 * Additional methods to the Array class
 */

/**
 * Gets array elements without duplicates
 */
Array.prototype.unique = function(){
    var index = {}, 
        list = [],
        size = this.length;
    for(var i = 0; i < size; i++){
        if(index.hasOwnProperty(this[i]))
            continue;
        list.push(this[i]);
        index[this[i]] = 1;
    }
    return list;
}
