var Layer = {
  props: {
    pane: {
      type: String,
      default: 'overlayPane'
    },
    attribution: {
      type: String,
      default: null
    },
    name: {
      type: String,
      custom: true,
      default: undefined
    },
    layerType: {
      type: String,
      custom: true,
      default: undefined
    },
    visible: {
      type: Boolean,
      custom: true,
      default: true
    }
  },
  mounted: function mounted () {
    this.layerOptions = {
      attribution: this.attribution,
      pane: this.pane
    };
  },
  beforeDestroy: function beforeDestroy () {
    this.unbindPopup();
    this.unbindTooltip();
    this.parentContainer.removeLayer(this);
  },
  methods: {
    setAttribution: function setAttribution (val, old) {
      var attributionControl = this.$parent.mapObject.attributionControl;
      attributionControl.removeAttribution(old).addAttribution(val);
    },
    setName: function setName (newVal, oldVal) {
      if (newVal === oldVal) { return; }
      this.parentContainer.removeLayer(this);
      if (this.visible) {
        this.parentContainer.addLayer(this);
      }
    },
    setLayerType: function setLayerType (newVal, oldVal) {
      if (newVal === oldVal) { return; }
      this.parentContainer.removeLayer(this);
      if (this.visible) {
        this.parentContainer.addLayer(this);
      }
    },
    setVisible: function setVisible (newVal, oldVal) {
      if (newVal === oldVal) { return; }
      if (this.mapObject) {
        if (newVal) {
          this.parentContainer.addLayer(this);
        } else {
          this.parentContainer.removeLayer(this);
        }
      }
    },
    unbindTooltip: function unbindTooltip () {
      var tooltip = this.mapObject ? this.mapObject.getTooltip() : null;
      if (tooltip) {
        tooltip.unbindTooltip();
      }
    },
    unbindPopup: function unbindPopup () {
      var popup = this.mapObject ? this.mapObject.getPopup() : null;
      if (popup) {
        popup.unbindPopup();
      }
    }
  }
};

var InteractiveLayer = {
  props: {
    interactive: {
      type: Boolean,
      default: true
    },
    bubblingMouseEvents: {
      type: Boolean,
      default: true
    }
  },
  mounted: function mounted () {
    this.interactiveLayerOptions = {
      interactive: this.interactive,
      bubblingMouseEvents: this.bubblingMouseEvents
    };
  }
};

var Path = {
  mixins: [Layer, InteractiveLayer],
  props: {
    lStyle: {
      type: Object,
      custom: true,
      default: null
    },
    stroke: {
      type: Boolean,
      custom: true,
      default: true
    },
    color: {
      type: String,
      custom: true,
      default: '#3388ff'
    },
    weight: {
      type: Number,
      custom: true,
      default: 3
    },
    opacity: {
      type: Number,
      custom: true,
      default: 1.0
    },
    lineCap: {
      type: String,
      custom: true,
      default: 'round'
    },
    lineJoin: {
      type: String,
      custom: true,
      default: 'round'
    },
    dashArray: {
      type: String,
      custom: true,
      default: null
    },
    dashOffset: {
      type: String,
      custom: true,
      default: null
    },
    fill: {
      type: Boolean,
      custom: true,
      default: false
    },
    fillColor: {
      type: String,
      custom: true,
      default: '#3388ff'
    },
    fillOpacity: {
      type: Number,
      custom: true,
      default: 0.2
    },
    fillRule: {
      type: String,
      custom: true,
      default: 'evenodd'
    },
    className: {
      type: String,
      custom: true,
      default: null
    }
  },
  mounted: function mounted () {
    this.pathOptions = Object.assign({}, this.layerOptions,
      this.interactiveLayerOptions,
      {stroke: this.stroke,
      color: this.color,
      weight: this.weight,
      opacity: this.opacity,
      lineCap: this.lineCap,
      lineJoin: this.lineJoin,
      dashArray: this.dashArray,
      dashOffset: this.dashOffset,
      fill: this.fill,
      fillColor: this.fillColor,
      fillOpacity: this.fillOpacity,
      fillRule: this.fillRule,
      className: this.className});

    if (this.lStyle) {
      console.warn('lStyle is deprecated and is going to be removed in the next major version');
      for (var style in this.lStyle) {
        this.pathOptions[style] = this.lStyle[style];
      }
    }
  },
  beforeDestroy: function beforeDestroy () {
    if (this.parentContainer) {
      this.parentContainer.removeLayer(this);
    } else {
      console.error('Missing parent container');
    }
  },
  methods: {
    setLStyle: function setLStyle (newVal) {
      this.mapObject.setStyle(newVal);
    },
    setStroke: function setStroke (newVal, oldVal) {
      if (newVal === oldVal) { return; }
      this.mapObject.setStyle({ stroke: newVal });
    },
    setColor: function setColor (newVal, oldVal) {
      if (newVal === oldVal) { return; }
      if (newVal !== undefined && newVal !== null) {
        this.mapObject.setStyle({ color: newVal });
      }
    },
    setWeight: function setWeight (newVal, oldVal) {
      if (newVal === oldVal) { return; }
      if (newVal) {
        this.mapObject.setStyle({ weight: newVal });
      }
    },
    setOpacity: function setOpacity (newVal, oldVal) {
      if (newVal === oldVal) { return; }
      if (newVal !== undefined && newVal !== null) {
        this.mapObject.setStyle({ opacity: newVal });
      }
    },
    setLineCap: function setLineCap (newVal, oldVal) {
      if (newVal === oldVal) { return; }
      if (newVal) {
        this.mapObject.setStyle({ lineCap: newVal });
      }
    },
    setLineJoin: function setLineJoin (newVal, oldVal) {
      if (newVal === oldVal) { return; }
      if (newVal) {
        this.mapObject.setStyle({ lineJoin: newVal });
      }
    },
    setDashArray: function setDashArray (newVal, oldVal) {
      if (newVal === oldVal) { return; }
      if (newVal) {
        this.mapObject.setStyle({ dashArray: newVal });
      }
    },
    setDashOffset: function setDashOffset (newVal, oldVal) {
      if (newVal === oldVal) { return; }
      if (newVal) {
        this.mapObject.setStyle({ dashOffset: newVal });
      }
    },
    setFill: function setFill (newVal, oldVal) {
      if (newVal === oldVal) { return; }
      this.mapObject.setStyle({ fill: newVal });
    },
    setFillColor: function setFillColor (newVal, oldVal) {
      if (newVal === oldVal) { return; }
      if (newVal) {
        this.mapObject.setStyle({ fillColor: newVal });
      }
    },
    setFillOpacity: function setFillOpacity (newVal, oldVal) {
      if (newVal === oldVal) { return; }
      if (newVal) {
        this.mapObject.setStyle({ fillOpacity: newVal });
      }
    },
    setFillRule: function setFillRule (newVal, oldVal) {
      if (newVal === oldVal) { return; }
      if (newVal) {
        this.mapObject.setStyle({ fillRule: newVal });
      }
    },
    setClassName: function setClassName (newVal, oldVal) {
      if (newVal === oldVal) { return; }
      if (newVal) {
        this.mapObject.setStyle({ className: newVal });
      }
    }
  }
};

export default Path;