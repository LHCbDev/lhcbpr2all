/** The Menu class
 *  It represents the links on the sidebar
 */

/**
 * Constructor
 */
var Menu = function(app){
    this.app = app;
    this.items = [];
}

/**
 * Add items to the menu
 */
Menu.prototype.add = function(item) {
    var self = this;
    if(Array === item.constructor){
        item.forEach(function(element){
            self.add(element);
        });
    } else {
        self.items.push(item);
    }
};

/**
 * Getter for all items
 */
Menu.prototype.getItems = function() {
    return this.items;
};
