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

var GridLayer = {
  mixins: [Layer],
  props: {
    pane: {
      type: String,
      default: 'tilePane'
    },
    opacity: {
      type: Number,
      custom: false,
      default: 1.0
    },
    zIndex: {
      type: Number,
      default: 1
    },
    tileSize: {
      type: Number,
      default: 256
    },
    noWrap: {
      type: Boolean,
      default: false
    }
  },
  mounted: function mounted () {
    this.gridLayerOptions = Object.assign({}, this.layerOptions,
      {pane: this.pane,
      opacity: this.opacity,
      zIndex: this.zIndex,
      tileSize: this.tileSize,
      noWrap: this.noWrap});
  }
};

var TileLayer = {
  mixins: [GridLayer],
  props: {
    tms: {
      type: Boolean,
      default: false
    },
    detectRetina: {
      type: Boolean,
      default: false
    }
  },
  mounted: function mounted () {
    this.tileLayerOptions = Object.assign({}, this.gridLayerOptions,
      {tms: this.tms,
      detectRetina: this.detectRetina});
  },
  render: function render () {
    return null;
  }
};

var TileLayerWMS = {
  mixins: [TileLayer],
  props: {
    layers: {
      type: String,
      default: ''
    },
    styles: {
      type: String,
      default: ''
    },
    format: {
      type: String,
      default: 'image/jpeg'
    },
    transparent: {
      type: Boolean,
      custom: false
    },
    version: {
      type: String,
      default: '1.1.1'
    },
    crs: {
      default: null
    },
    upperCase: {
      type: Boolean,
      default: false
    }
  },
  mounted: function mounted () {
    this.tileLayerWMSOptions = Object.assign({}, this.tileLayerOptions,
      {layers: this.layers,
      styles: this.styles,
      format: this.format,
      transparent: this.transparent,
      version: this.version,
      crs: this.crs,
      upperCase: this.upperCase});
  }
};

export default TileLayerWMS;